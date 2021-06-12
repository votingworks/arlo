import React, { useState, useRef, useEffect } from 'react'
import styled from 'styled-components'
import { select, json, geoPath, geoAlbers } from 'd3'
import { feature, mesh } from 'topojson-client'
// topojson-specification is defined in package.json but throwing linting error here
// eslint-disable-next-line import/no-unresolved
import { GeometryObject, Topology } from 'topojson-specification'
import { Feature } from 'geojson'
import { Colors } from '@blueprintjs/core'
import labelValueStates from '../AASetup/Settings/states'
import { JurisdictionRoundStatus, IJurisdiction } from '../useJurisdictions'
import { FileProcessingStatus, IFileInfo } from '../useCSV'

interface IProps {
  stateName?: string | null
  jurisdictions: IJurisdiction[]
}

const SVGMap = styled.svg`
  margin-bottom: 30px;
  .outline {
    fill: none;
    stroke: ${Colors.BLACK};
    stroke-width: 1.5px;
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
  #land {
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

const Map = ({ stateName, jurisdictions }: IProps) => {
  const width = 960
  const height = 500
  const d3Container = useRef(null)
  const tooltipContainer = useRef(null)

  const projection = geoAlbers()

  const path = geoPath().projection(projection)

  const [usCounties, setUSCounties] = useState<Feature[] | undefined>(undefined)
  const [usStates, setUSStates] = useState<Feature[] | undefined>(undefined)
  const [usState, setUSState] = useState<Feature | undefined>(undefined)
  const [jsonData, setJsonData] = useState<Topology | undefined>(undefined)

  const getStateName = (abbr: string) => {
    const filteredState = labelValueStates.find(
      ({ value, label }) => value === abbr && label
    )
    return filteredState && filteredState.label
  }

  const getJurisdictionStatus = (countyName: string) => {
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
        if (currentRoundStatus.status === JurisdictionRoundStatus.IN_PROGRESS) {
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
    return ''
  }

  const loadMapData = async () => {
    const respJsonData: Topology | undefined = await json(
      '/us-states-counties.json'
    )
    if (respJsonData && respJsonData.objects) {
      setUSStates(
        (feature(
          respJsonData,
          respJsonData.objects.states
        ) as GeoJSON.FeatureCollection).features
      )
      setUSState(
        (feature(
          respJsonData,
          respJsonData.objects.states
        ) as GeoJSON.FeatureCollection).features.filter(
          d =>
            d &&
            d.properties &&
            stateName &&
            d.properties.name === getStateName(stateName)
        )[0]
      )
      setUSCounties(
        (feature(
          respJsonData,
          respJsonData.objects.counties
        ) as GeoJSON.FeatureCollection).features
      )
      setJsonData(respJsonData)
    }
  }

  useEffect(() => {
    loadMapData()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (stateName && d3Container.current && tooltipContainer.current) {
      const svgElement = select(d3Container.current)

      if (jsonData && usStates && usState && usCounties) {
        projection.fitSize([width, height], usState)

        svgElement
          .append('path')
          .datum(
            mesh(
              (jsonData as unknown) as Topology,
              jsonData.objects.states as GeometryObject,
              (a: GeometryObject, b: GeometryObject) => a !== b
            )
          )
          .attr('class', 'mesh')
          .attr('d', path)

        svgElement
          .append('path')
          .datum(usState)
          .attr('class', 'outline')
          .attr('d', path)
          .attr('id', 'land')

        svgElement
          .append('g')
          .attr('id', 'states')
          .selectAll('path')
          .data(usStates)
          .enter()
          .append('path')
          .attr('d', path)
          .attr('className', 'state')
          .attr('fill', '#aaa')

        svgElement
          .append('clipPath')
          .attr('id', 'clip-land')
          .append('use')
          .attr('xlink:href', '#land')

        svgElement
          .selectAll('path')
          .data(usCounties)
          .enter()
          .append('path')
          .attr('d', path)
          .attr('clip-path', 'url(#clip-land)')
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
              .style('left', `${event.pageX + 10}px`)
              .style('top', `${event.pageY}px`)
              .html(event.toElement.__data__.properties.name)
          })
          .on('mouseout', () => {
            select('#tooltip').style('display', 'none')
          })
      }
    }
  }, [jsonData]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <>
      <SVGMap
        className="d3-component"
        width={width}
        height={height}
        ref={d3Container}
      />
      <Tooltip id="tooltip" className="hide-tooltip" ref={tooltipContainer} />
    </>
  )
}

export default Map
