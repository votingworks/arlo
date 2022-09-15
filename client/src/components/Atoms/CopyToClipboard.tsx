import React, { useState } from 'react'
import copy from 'copy-to-clipboard'
import { Button } from '@blueprintjs/core'
import { useIsMounted } from '../utilities'

const CopyToClipboard: React.FC<{
  getText: () => string
}> = ({ getText }) => {
  const [copied, setCopied] = useState(false)
  const isMounted = useIsMounted()
  return (
    <Button
      icon={copied ? 'tick-circle' : 'clipboard'}
      onClick={() => {
        const success = copy(getText(), { format: 'text/html' })
        if (success) {
          setCopied(true)
          setTimeout(() => {
            if (isMounted()) setCopied(false)
          }, 3000)
        }
      }}
      style={{ width: '160px' }}
    >
      {copied ? 'Copied' : 'Copy to clipboard'}
    </Button>
  )
}

export default CopyToClipboard
