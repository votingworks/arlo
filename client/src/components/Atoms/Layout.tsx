import styled, { css } from 'styled-components'

interface BoxProps {
  justify?: 'start' | 'center' | 'end' | 'space-between' | 'space-around'
  align?: 'start' | 'center' | 'end' | 'stretch' | 'baseline'
  gap?: string
}

const Box = styled.div<BoxProps>`
  display: flex;
  ${props =>
    props.justify &&
    css`
      justify-content: ${props.justify};
    `}
  ${props =>
    props.align &&
    css`
      align-items: ${props.align};
    `}
  ${props =>
    props.gap &&
    css`
      gap: ${props.gap};
    `};
`

/**
 * Convenience component for a flexbox with flex-direction=row.
 *
 * Example:
 *  <Row justify="space-between" align="center" gap="20px">
 *    ... items ...
 *  </Row>
 */
export const Row = styled(Box)`
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
export const Column = styled(Box)`
  flex-direction: column;
`

export const ButtonRow = styled(Row).attrs({ gap: '10px' })``
