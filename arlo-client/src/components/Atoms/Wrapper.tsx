import styled from 'styled-components'

export const Wrapper = styled.div`
  display: flex;
  flex-direction: column;
  width: 100%;

  &.single-page {
    flex-direction: column;
    align-items: center;
    &.left {
      align-items: flex-start;
    }
  }
`

export const Inner = styled.div`
  display: flex;
  margin-right: auto;
  margin-left: auto;
  width: 1020px;
  min-width: 1020px;
  padding: 0 15px;
`

export default Wrapper
