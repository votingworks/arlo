import React, { useState } from 'react'
import { IButtonProps, Button } from '@blueprintjs/core'

interface IAsyncButtonProps extends IButtonProps {
  onClick: () => Promise<unknown>
}

const AsyncButton: React.FC<IAsyncButtonProps> = (props: IAsyncButtonProps) => {
  const [isSubmitting, setIsSubmitting] = useState(false)
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
          setIsSubmitting(false)
        }
      }}
    />
  )
}

export default AsyncButton
