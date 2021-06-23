import React, { useState, useRef, useEffect, useCallback } from 'react'
import styled from 'styled-components'
import { select, json, geoPath, geoAlbers } from 'd3'
import { feature } from 'topojson-client'
// topojson-specification is defined in package.json but throwing linting error here
// eslint-disable-next-line import/no-unresolved
import { Topology } from 'topojson-specification'
import { Feature } from 'geojson'
import { Colors, Spinner } from '@blueprintjs/core'
import labelValueStates from '../AASetup/Settings/states'
import { JurisdictionRoundStatus, IJurisdiction } from '../useJurisdictions'
import { FileProcessingStatus, IFileInfo } from '../useCSV'

interface IProps {
  stateName?: string | null
  jurisdictions: IJurisdiction[]
  isRoundStarted: boolean
  auditType:
    | 'BALLOT_POLLING'
    | 'BATCH_COMPARISON'
    | 'BALLOT_COMPARISON'
    | 'HYBRID'
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
    cursor: pointer;
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
  .progress {
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
  &.progress {
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

const Map = ({
  stateName,
  jurisdictions,
  isRoundStarted,
  auditType,
}: IProps) => {
  const width = 960
  const height = 500
  const d3Container = useRef(null)
  const tooltipContainer = useRef(null)

  const [usCounties, setUSCounties] = useState<Feature[] | undefined>(undefined)
  const [usStates, setUSStates] = useState<Feature[] | undefined>(undefined)
  const [usState, setUSState] = useState<Feature | undefined>(undefined)
  const [jsonData, setJsonData] = useState<Topology | undefined>(undefined)
  const [isMapLoaded, setIsMapLoaded] = useState<boolean>(false)

  const getStateName = (abbr: string) => {
    const filteredState = labelValueStates.find(
      ({ value, label }) => value === abbr && label
    )
    return filteredState && filteredState.label
  }

  const getJurisdictionStatus = useCallback(
    (countyName: string) => {
      const filteredJurisdiction = jurisdictions.find(
        jurisdiction => jurisdiction.name === countyName
      )

      if (filteredJurisdiction) {
        const {
          currentRoundStatus,
          ballotManifest,
          batchTallies,
          cvrs,
        } = filteredJurisdiction

        if (!currentRoundStatus) {
          const files: IFileInfo['processing'][] = [ballotManifest.processing]
          if (batchTallies) files.push(batchTallies.processing)
          if (cvrs) files.push(cvrs.processing)

          const numComplete = files.filter(
            f => f && f.status === FileProcessingStatus.PROCESSED
          ).length
          const anyFailed = files.some(
            f => f && f.status === FileProcessingStatus.ERRORED
          )

          // Special case when we just have a ballotManifest
          if (files.length === 1) {
            if (anyFailed) {
              return 'danger'
            }
            if (numComplete === 1) {
              return 'success'
            }
            return 'gray'
          }

          // When we have multiple files
          if (anyFailed) {
            return 'danger'
          }
          if (numComplete === files.length) {
            return 'gray'
          }
        } else {
          if (currentRoundStatus.status === JurisdictionRoundStatus.COMPLETE) {
            return 'success'
          }
          if (
            currentRoundStatus.status === JurisdictionRoundStatus.IN_PROGRESS
          ) {
            return 'progress'
          }
          if (
            currentRoundStatus.status === JurisdictionRoundStatus.NOT_STARTED ||
            currentRoundStatus.status === null
          ) {
            return 'gray'
          }
        }
      }
      return 'default'
    },
    [jurisdictions]
  )

  useEffect(() => {
    const loadMapData = async () => {
      let respJsonData: Topology | undefined
      try {
        respJsonData = await json(
          'https://cdn.jsdelivr.net/npm/us-atlas@3/counties-10m.json'
        )
      } catch (error) {
        // eslint-disable-next-line no-console
        console.error(`File Error: ${error}`)
        // use local topojson file if CDN link fails to load
        respJsonData = await json('/us-states-counties.json')
      }

      if (respJsonData && respJsonData.objects) {
        setUSStates(
          (feature(
            respJsonData,
            respJsonData.objects.states
          ) as GeoJSON.FeatureCollection).features
        )
        const singleState = (feature(
          respJsonData,
          respJsonData.objects.states
        ) as GeoJSON.FeatureCollection).features.filter(
          d =>
            d &&
            d.properties &&
            stateName &&
            d.properties.name === getStateName(stateName)
        )[0]

        setUSState(singleState)

        // county ID's initial 2 characters are of state
        // hence, just setting counties of audit state
        setUSCounties(
          (feature(
            respJsonData,
            respJsonData.objects.counties
          ) as GeoJSON.FeatureCollection).features.filter(
            (d, i) =>
              d &&
              d.id &&
              singleState &&
              singleState.id &&
              d.id.toString().slice(0, 2) === singleState.id.toString()
          )
        )
        setJsonData(respJsonData)
      }
    }

    loadMapData()
  }, [stateName])

  useEffect(() => {
    const projection = geoAlbers()
    const path = geoPath().projection(projection)

    if (d3Container.current && tooltipContainer.current) {
      const svgElement = select(d3Container.current)

      if (jsonData && usStates && usState && usCounties) {
        projection.fitSize([width, height], usState)

        svgElement
          .append('path')
          .datum(usState)
          .attr('class', 'outline')
          .attr('d', path)
          .attr('id', 'single-state')

        svgElement
          .append('clipPath')
          .attr('id', 'clip-state')
          .append('use')
          .attr('xlink:href', '#single-state')

        svgElement
          .selectAll('path')
          .data(usCounties)
          .enter()
          .append('path')
          .attr('d', path)
          .attr('clip-path', 'url(#clip-state)')
          .attr('class', d => {
            let statusClass = ''
            if (d && d.properties) {
              statusClass = getJurisdictionStatus(d.properties.name)
            }
            return `county ${statusClass}`
          })
          .on('mouseover', event => {
            select(tooltipContainer.current)
              .style('display', 'block')
              .style('left', `${event.offsetX + 10}px`)
              .style('top', `${event.offsetY}px`)
              .html(event.toElement.__data__.properties.name)
          })
          .on('mouseout', () => {
            select('#tooltip').style('display', 'none')
          })

        setIsMapLoaded(true)
      }
    }
  }, [jsonData, getJurisdictionStatus, usStates, usState, usCounties])

  return (
    <MapWrapper>
      <SVGMap
        className="d3-component"
        width={width}
        height={height}
        ref={d3Container}
      />
      <Tooltip id="tooltip" className="hide-tooltip" ref={tooltipContainer} />
      {isMapLoaded ? (
        <MapLabels>
          {isRoundStarted ? (
            <div>
              <MapLabelsRow>
                <MapLabelsBoxes className="success" /> Complete
              </MapLabelsRow>
              <MapLabelsRow>
                <MapLabelsBoxes className="progress" /> In-progress
              </MapLabelsRow>
              <MapLabelsRow>
                <MapLabelsBoxes className="gray" /> Not Started
              </MapLabelsRow>
              <MapLabelsRow>
                <MapLabelsBoxes className="default" /> Non-Participating
                Jurisdiction
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
                <MapLabelsBoxes className="gray" /> No Manifest uploaded
              </MapLabelsRow>
              <MapLabelsRow>
                <MapLabelsBoxes className="default" /> Non-Participating
                Jurisdiction
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
                <MapLabelsBoxes className="gray" /> No files uploaded
              </MapLabelsRow>
              <MapLabelsRow>
                <MapLabelsBoxes className="default" /> Non-Participating
                Jurisdiction
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
