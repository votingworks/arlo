import React from 'react'
import QRCode from 'qrcode.react'
import styled from 'styled-components'

const QRroot = styled.div`
  display: none;
`

const QRs: React.FC<{ passphrases: string[] }> = ({
  passphrases,
}: {
  passphrases: string[]
}) => {
  return (
    <QRroot id="qr-root">
      {passphrases.map(passphrase => (
        <span key={passphrase} id={`qr-${passphrase}`}>
          <QRCode
            value={`${window.location.origin}/auditboard/${passphrase}`}
            size={200}
          />
        </span>
      ))}
    </QRroot>
  )
}

export default QRs
