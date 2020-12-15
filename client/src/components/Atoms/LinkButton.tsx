import React from 'react'
import { Link, LinkProps } from 'react-router-dom'
import { Button, IButtonProps } from '@blueprintjs/core'

interface ILinkButtonProps
  extends LinkProps,
    Pick<
      IButtonProps,
      'disabled' | 'intent' | 'large' | 'fill' | 'minimal' | 'icon'
    > {}

// LinkButton creates a React Router Link that uses a BlueprintJS button instead
// of an anchor tag. This allows us to disable links (and gives us nice button
// styling).
const LinkButton = (props: ILinkButtonProps) => {
  return (
    <Link
      {...props}
      component={({ navigate, ...rest }) => (
        <Button onClick={navigate} {...rest} />
      )}
    />
  )
}

export default LinkButton
