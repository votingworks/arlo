import styled from 'styled-components'

export const Wrapper = styled.main`
  display: flex;
  flex-direction: column;
  width: 100%;
  padding-bottom: 30px;
`

interface IInnerProps {
  flexDirection?: 'column' | 'row'
  withTopPadding?: boolean
}

export const Inner = styled.section<IInnerProps>`
  display: flex;
  margin-right: auto;
  margin-left: auto;
  width: 100%;
  max-width: 1020px;
  padding: 0 30px;
  padding-top: ${props => (props.withTopPadding ? '30px' : undefined)};
  flex-direction: ${props => props.flexDirection || undefined};
`

export const SupportToolsInner = styled.div`
  display: flex;
  justify-content: center;
  margin-left: auto;
  margin-right: auto;
  padding: 30px 150px;
  width: 100%;
`

export default Wrapper
