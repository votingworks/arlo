import styled, { css } from 'styled-components'

export interface IFlexboxProps {
  justifyContent?: 'start' | 'center' | 'end' | 'space-between' | 'space-around'
  alignItems?: 'start' | 'center' | 'end' | 'stretch' | 'baseline'
  gap?: string
}

const Flexbox = styled.div<IFlexboxProps>`
  display: flex;
  ${props =>
    props.justifyContent &&
    css`
      justify-content: ${props.justifyContent};
    `}
  ${props =>
    props.alignItems &&
    css`
      align-items: ${props.alignItems};
    `}
  ${props =>
    props.gap &&
    css`
      gap: ${props.gap};
    `};
`

/**
 * Convenience component for a flexbox with flex-direction set based on media query.
 *
 * Example:
 *  <FlexContainer justify="space-between" align="center" gap="20px">
 *    ... items ...
 *  </FlexContainer>
 */
export const FlexContainer = styled(Flexbox)`
  flex-direction: row;

  @media (max-width: 480px) {
    flex-direction: column;
  }
`

/**
 * Convenience component for a flexbox with flex-direction=row.
 *
 * Example:
 *  <Row justify="space-between" align="center" gap="20px">
 *    ... items ...
 *  </Row>
 */
export const Row = styled(Flexbox)`
  flex-direction: row;
`

/**
 * Convenience component for a flexbox with flex-direction=column
 *
 * Example:
 *  <Column justify="space-between" align="stretch" gap="20px">
 *    ... items ...
 *  </Row>
 */
export const Column = styled(Flexbox)`
  flex-direction: column;
`

export const ButtonRow = styled(Row).attrs({ gap: '10px' })``
