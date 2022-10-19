import React, { useState } from 'react'
import copy from 'copy-to-clipboard'
import { Button } from '@blueprintjs/core'
import { useIsMounted } from '../utilities'

const CopyToClipboard: React.FC<{
  getText: () => { text: string; format: 'text/plain' | 'text/html' }
  label?: string
  copiedLabel?: string
}> = ({ getText, label = 'Copy to clipboard', copiedLabel = 'Copied' }) => {
  const [copied, setCopied] = useState(false)
  const isMounted = useIsMounted()
  return (
    <Button
      icon={copied ? 'tick-circle' : 'clipboard'}
      onClick={() => {
        const { text, format } = getText()
        const success = copy(text, { format })
        if (success) {
          setCopied(true)
          setTimeout(() => {
            if (isMounted()) setCopied(false)
          }, 3000)
        }
      }}
      style={{
        minWidth: `${Math.max(label.length, copiedLabel.length)}em`,
      }}
    >
      {copied ? copiedLabel : label}
    </Button>
  )
}

export default CopyToClipboard
