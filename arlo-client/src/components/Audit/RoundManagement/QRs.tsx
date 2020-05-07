import React from 'react'
import QRCode from 'qrcode.react'
import styled from 'styled-components'

const QRroot = styled.div`
  display: none;
`

const QRs: React.FC<{ electionId: string; boardIds: string[] }> = ({
  electionId,
  boardIds,
}: {
  electionId: string
  boardIds: string[]
}) => {
  return (
    <QRroot id="qr-root">
      {boardIds.map(id => (
        <span key={id} id={`qr-${id}`}>
          <QRCode
            value={`${window.location.origin}/election/${electionId}/audit-board/${id}`}
            size={200}
          />
        </span>
      ))}
    </QRroot>
  )
}

export default QRs
