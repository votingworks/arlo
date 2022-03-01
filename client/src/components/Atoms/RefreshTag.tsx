import React, { useState } from 'react'
import styled from 'styled-components'
import { Tag } from '@blueprintjs/core'
import { useInterval } from '../utilities'

const RefreshStatusTag = styled(Tag)`
  margin-top: 20px;
  width: 14em;
  text-align: center;
`

export const prettifyRefreshStatus = (refreshTime: number) => {
  if (refreshTime < 240000)
    return `Will refresh in ${5 - Math.floor(refreshTime / 60000)} minutes`
  if (refreshTime < 250000) return `Will refresh in 1 minute`
  return `Will refresh in ${Math.ceil((300000 - refreshTime) / 10000) *
    10} seconds`
}

export const RefreshTag = ({ refresh }: { refresh: () => void }) => {
  const [lastRefreshTime, setLastRefreshTime] = useState(Date.now())
  const [time, setTime] = useState(Date.now())

  // poll the apis every 5 minutes
  useInterval(() => {
    const now = Date.now()
    if (now - lastRefreshTime >= 1000 * 60 * 5) {
      setLastRefreshTime(now)
      refresh()
    }
    setTime(now)
  }, 1000)

  return (
    <RefreshStatusTag>
      {prettifyRefreshStatus(time - lastRefreshTime)}
    </RefreshStatusTag>
  )
}
