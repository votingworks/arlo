import React, { useState } from 'react'
import copy from 'copy-to-clipboard'
import { Button } from '@blueprintjs/core'
import { useIsMounted } from '../utilities'

const CopyToClipboard: React.FC<{
  getText: () => { text: string; format: 'text/plain' | 'text/html' }
  label?: string
  copiedLabel?: string
  iconOnly?: boolean
}> = ({
  getText,
  label = 'Copy to clipboard',
  copiedLabel = 'Copied',
  iconOnly = false,
}) => {
  const [copied, setCopied] = useState(false)
  const isMounted = useIsMounted()
  const buttonText = copied ? copiedLabel : label
  return (
    <Button
      small={iconOnly}
      minimal={iconOnly}
      title={iconOnly ? buttonText : undefined}
      aria-label={iconOnly ? buttonText : undefined}
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
      style={
        iconOnly
          ? undefined
          : { minWidth: `${Math.max(label.length, copiedLabel.length)}em` }
      }
    >
      {!iconOnly && buttonText}
    </Button>
  )
}

export default CopyToClipboard
