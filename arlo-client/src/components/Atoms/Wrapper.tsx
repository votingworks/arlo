import styled from 'styled-components'

const Wrapper = styled.div`
  display: flex;
  flex-wrap: wrap;
  margin-top: 20px;
  margin-right: auto;
  margin-left: auto;
  width: 100%;
  max-width: 1020px;
  padding-right: 15px;
  padding-left: 15px;

  &.single-page {
    flex-direction: column;
    align-items: center;
  }
`

export default Wrapper
