import React, { useState, CSSProperties } from 'react'
import { IButtonProps, Button } from '@blueprintjs/core'
import { useIsMounted } from '../utilities'

interface IAsyncButtonProps extends IButtonProps {
  onClick: () => Promise<unknown>
  style?: CSSProperties
}

const AsyncButton: React.FC<IAsyncButtonProps> = (props: IAsyncButtonProps) => {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const isMounted = useIsMounted()
  return (
    <Button
      {...props}
      loading={isSubmitting}
      onClick={async () => {
        setIsSubmitting(true)
        try {
          await props.onClick()
        } catch (e) {
          // Errors should be handled within onClick
          console.error(e) // eslint-disable-line no-console
        } finally {
          if (isMounted()) setIsSubmitting(false)
        }
      }}
    />
  )
}

export default AsyncButton
