import styled from 'styled-components'

export const Wrapper = styled.main.attrs({
  id: 'main',
  tabIndex: -1,
})`
  display: flex;
  flex-direction: column;
  width: 100%;
  padding-bottom: 30px;
`

interface IInnerProps {
  flexDirection?: 'column' | 'row'
  justifyContent?: 'start' | 'center' | 'space-between'
  withTopPadding?: boolean
}

const paddingTop = ({ withTopPadding }: IInnerProps): string | undefined =>
  withTopPadding ? '30px' : undefined
const flexDirection = ({
  flexDirection: value,
}: IInnerProps): IInnerProps['flexDirection'] => value
const justifyContent = ({
  justifyContent: value,
}: IInnerProps): IInnerProps['justifyContent'] => value

export const Inner = styled.section<IInnerProps>`
  display: flex;
  margin-right: auto;
  margin-left: auto;
  width: 100%;
  max-width: 1020px;
  padding: 0 30px;
  padding-top: ${paddingTop};
  flex-direction: ${flexDirection};
  justify-content: ${justifyContent};
`

export const SupportToolsInner = styled.div`
  display: flex;
  justify-content: center;
  margin-left: auto;
  margin-right: auto;
  padding: 30px 150px;
  width: 100%;

  @media (max-width: 480px) {
    padding: 30px;
  }
`

export default Wrapper
