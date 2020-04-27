import styled from 'styled-components'

const ContestsTable = styled.table`
  margin: 50px 0;
  width: 100%;
  text-align: left;
  line-height: 30px;

  td,
  th {
    padding: 0 10px;
  }
  thead {
    background-color: #137cbd;
    color: #ffffff;
  }
  tr:nth-child(even) {
    background-color: #f5f8fa;
  }
`

export default ContestsTable
