import React, { useState, useEffect } from 'react'
import styled from 'styled-components'
import { geoPath, geoAlbers } from 'd3-geo'
import { feature } from 'topojson-client'
// topojson-specification is defined in package.json but throwing linting error here
// eslint-disable-next-line import/no-unresolved
import { Topology } from 'topojson-specification'
import { Colors, Spinner } from '@blueprintjs/core'
import { IAuditSettings } from '../../useAuditSettings'
import {
  getJurisdictionStatus,
  JurisdictionProgressStatus,
  IJurisdiction,
} from '../../useJurisdictions'
import { states } from '../Setup/Settings/states'
import mapCountyCorrections from './map-county-corrections'

interface IProps {
  stateAbbreviation: string
  jurisdictions: IJurisdiction[]
  isRoundStarted: boolean
  auditType: IAuditSettings['auditType']
}

const MapWrapper = styled.div`
  position: relative;
`

const SVGMap = styled.svg`
  margin-bottom: 30px;
  .outline {
    fill: none;
    stroke: ${Colors.BLACK};
    stroke-width: 0.5px;
  }
  .mesh {
    fill: none;
    stroke-linejoin: round;
  }
  path {
    fill: none;
    stroke: none;
    stroke-width: 0.5px;
  }
  #single-state {
    stroke: ${Colors.BLACK};
  }
  .county {
    fill: ${Colors.WHITE};
    stroke: ${Colors.BLACK};
  }
  .county:hover {
    stroke-width: 2px;
  }
  .danger {
    fill: ${Colors.RED3};
  }
  .success {
    fill: ${Colors.GREEN4};
  }
  .progress-2 {
    fill: ${Colors.COBALT4};
  }
  .progress-1 {
    fill: ${Colors.ORANGE4};
  }
  .gray {
    fill: ${Colors.GRAY4};
  }
  .default {
    fill: ${Colors.WHITE};
  }
`

const Tooltip = styled.div`
  display: none;
  position: absolute;
  opacity: 0.9;
  border-radius: 3px;
  background: ${Colors.BLACK};
  padding: 5px;
  color: ${Colors.WHITE};
`

const MapLabels = styled.div`
  position: absolute;
  top: 0;
  z-index: 10;
`

const MapLabelsRow = styled.div`
  display: flex;
  align-items: center;
  margin-bottom: 5px;
`

const MapLabelsBoxes = styled.div`
  display: inline-block;
  margin-right: 10px;
  width: 20px;
  height: 20px;
  &.danger {
    background-color: ${Colors.RED3};
  }
  &.success {
    background-color: ${Colors.GREEN4};
  }
  &.progress-2 {
    background-color: ${Colors.COBALT4};
  }
  &.progress-1 {
    background-color: ${Colors.ORANGE4};
  }
  &.gray {
    background-color: ${Colors.GRAY4};
  }
  &.default {
    border: 1px solid ${Colors.BLACK};
  }
`

const MapSpinner = styled(Spinner)`
  position: absolute;
  top: 50%;
  right: 0;
  left: 0;
  transform: translateY(-50%);
  margin: 0 auto;
`

const Map: React.FC<IProps> = ({
  stateAbbreviation,
  jurisdictions,
  isRoundStarted,
  auditType,
}) => {
  const width = 960
  const height = 500

  const [jsonData, setJsonData] = useState<Topology | undefined>(undefined)
  const [tooltip, setTooltip] = useState<
    { text: string; left: number; top: number } | undefined
  >(undefined)

  const getJurisdictionStatusClass = (
    jurisdiction: IJurisdiction | undefined
  ) => {
    const jurisdictionStatus =
      jurisdiction && getJurisdictionStatus(jurisdiction)

    switch (jurisdictionStatus) {
      case JurisdictionProgressStatus.UPLOADS_COMPLETE:
      case JurisdictionProgressStatus.AUDIT_COMPLETE:
        return 'success'
      case JurisdictionProgressStatus.UPLOADS_FAILED:
        return 'danger'
      case JurisdictionProgressStatus.UPLOADS_IN_PROGRESS:
      case JurisdictionProgressStatus.AUDIT_IN_PROGRESS:
        return 'progress-2'
      case JurisdictionProgressStatus.UPLOADS_NOT_STARTED_LOGGED_IN:
      case JurisdictionProgressStatus.AUDIT_NOT_STARTED_LOGGED_IN:
        return 'progress-1'
      case JurisdictionProgressStatus.UPLOADS_NOT_STARTED_NO_LOGIN:
      case JurisdictionProgressStatus.AUDIT_NOT_STARTED_NO_LOGIN:
        return 'gray'
      default:
        return 'default'
    }
  }

  useEffect(() => {
    // Load topology data from a JSON file. This file is copied from:
    // https://www.npmjs.com/package/us-atlas#counties-10m.json @ v3.0.0
    const loadMapData = async () => {
      const response = await fetch('/us-states-counties.json')
      setJsonData(await response.json())
    }
    loadMapData()
  }, [])

  let mapContents: React.ReactNode = null
  if (jsonData) {
    const stateName = states[stateAbbreviation]
    const usState = (feature(
      jsonData,
      jsonData.objects.states
    ) as GeoJSON.FeatureCollection).features.find(
      state => state.properties!.name === stateName
    )
    if (!usState) throw new Error(`State topology not found: ${stateName}`)

    // Filter counties for this state. The county ID's initial 2 characters are
    // the state's ID
    const stateCounties = (feature(
      jsonData,
      jsonData.objects.counties
    ) as GeoJSON.FeatureCollection).features.filter(
      county => (county.id as string).slice(0, 2) === usState.id
    )

    const corrections = mapCountyCorrections[stateName] || {}
    const countyToJurisdiction = Object.fromEntries(
      stateCounties.map(county => {
        const countyName = (
          corrections[county.id!] || county.properties!.name
        ).toLowerCase()
        const matchingJurisdiction = jurisdictions.find(jurisdiction => {
          const jursidictionName = jurisdiction.name.toLowerCase()
          return (
            jursidictionName === countyName ||
            // Sometimes the jurisdiction name has "County" at the end, while
            // the county name in the topology does not
            jursidictionName === `${countyName} county`
          )
        })
        return [county.id, matchingJurisdiction]
      })
    )

    const numMatchedJurisdictions = Object.values(countyToJurisdiction).filter(
      j => j
    ).length
    if (numMatchedJurisdictions / jurisdictions.length < 0.5) return null

    const projection = geoAlbers().fitSize([width, height], usState)
    const path = geoPath().projection(projection)

    mapContents = (
      <>
        {stateCounties.map(county => {
          const jurisdiction = countyToJurisdiction[county.id!]
          return (
            <path
              key={county.id}
              d={path(county) || undefined}
              clipPath="url(#clip-state)"
              className={`county ${getJurisdictionStatusClass(jurisdiction)}`}
              onMouseOver={event =>
                setTooltip({
                  text: jurisdiction
                    ? jurisdiction.name
                    : county.properties!.name,
                  left: event.nativeEvent.offsetX + 10,
                  top: event.nativeEvent.offsetY,
                })
              }
              onMouseOut={() => setTooltip(undefined)}
            />
          )
        })}
        <path
          className="outline"
          d={path(usState) || undefined}
          id="single-state"
        />
        <clipPath id="clip-state">
          <use xlinkHref="#single-state" />
        </clipPath>
      </>
    )
  }

  return (
    <MapWrapper aria-hidden="true">
      <SVGMap
        className="d3-component"
        width={jsonData ? width : 0}
        height={jsonData ? height : 0}
      >
        {mapContents}
      </SVGMap>
      <Tooltip
        id="tooltip"
        style={
          tooltip && {
            display: 'block',
            left: `${tooltip.left}px`,
            top: `${tooltip.top}px`,
          }
        }
      >
        {tooltip?.text}
      </Tooltip>
      {jsonData ? (
        <MapLabels>
          {isRoundStarted ? (
            <div>
              <MapLabelsRow>
                <MapLabelsBoxes className="success" /> Complete
              </MapLabelsRow>
              <MapLabelsRow>
                <MapLabelsBoxes className="progress-2" /> In progress
              </MapLabelsRow>
              <MapLabelsRow>
                <MapLabelsBoxes className="progress-1" /> Logged in
              </MapLabelsRow>
              <MapLabelsRow>
                <MapLabelsBoxes className="gray" /> Not logged in
              </MapLabelsRow>
              <MapLabelsRow>
                <MapLabelsBoxes className="default" /> No data
              </MapLabelsRow>
            </div>
          ) : auditType === 'BALLOT_POLLING' ? (
            <div>
              <MapLabelsRow>
                <MapLabelsBoxes className="success" /> Manifest uploaded
              </MapLabelsRow>
              <MapLabelsRow>
                <MapLabelsBoxes className="danger" /> Manifest upload failed
              </MapLabelsRow>
              <MapLabelsRow>
                <MapLabelsBoxes className="progress-1" /> Logged in
              </MapLabelsRow>
              <MapLabelsRow>
                <MapLabelsBoxes className="gray" /> Not logged in
              </MapLabelsRow>
              <MapLabelsRow>
                <MapLabelsBoxes className="default" /> No data
              </MapLabelsRow>
            </div>
          ) : (
            <div>
              <MapLabelsRow>
                <MapLabelsBoxes className="success" /> All files uploaded
              </MapLabelsRow>
              <MapLabelsRow>
                <MapLabelsBoxes className="danger" /> File upload failed
              </MapLabelsRow>
              <MapLabelsRow>
                <MapLabelsBoxes className="progress-2" /> Uploads in progress
              </MapLabelsRow>
              <MapLabelsRow>
                <MapLabelsBoxes className="progress-1" /> Logged in
              </MapLabelsRow>
              <MapLabelsRow>
                <MapLabelsBoxes className="gray" /> Not logged in
              </MapLabelsRow>
              <MapLabelsRow>
                <MapLabelsBoxes className="default" /> No data
              </MapLabelsRow>
            </div>
          )}
        </MapLabels>
      ) : (
        <MapSpinner size={Spinner.SIZE_STANDARD} />
      )}
    </MapWrapper>
  )
}

export default Map
