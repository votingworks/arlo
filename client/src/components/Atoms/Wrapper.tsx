import styled from 'styled-components'

export const Wrapper = styled.div`
  display: flex;
  flex-direction: column;
  width: 100%;
  padding-bottom: 30px;
`

interface IInnerProps {
  flexDirection?: 'column' | 'row'
  withTopPadding?: boolean
}

export const Inner = styled.div<IInnerProps>`
  display: flex;
  margin-right: auto;
  margin-left: auto;
  width: 100%;
  max-width: 1020px;
  padding: 0 30px;
  padding-top: ${props => (props.withTopPadding ? '30px' : undefined)};
  flex-direction: ${props => props.flexDirection || undefined};
`

export default Wrapper
