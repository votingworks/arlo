import styled from 'styled-components'
import { Form } from 'formik'
import { RadioGroup } from '@blueprintjs/core'

export const BallotRow = styled.div`
  display: flex;
  justify-content: flex-start;
  margin: 20px 0;

  .ballot-side {
    width: 200px;
    padding: 20px 0;
  }
  .ballot-main {
    width: 50%;
    padding: 20px;
  }

  @media (max-width: 775px) {
    flex-direction: column;
    margin: 0;

    .ballot-side {
      padding: 20px;
    }

    .ballot-main {
      width: unset;
    }

    &:last-child {
      .ballot-side {
        display: none;
      }
    }
  }
`

export const FormBlock = styled(Form)`
  background-color: #ced9e0;
  padding: 20px;
`

export const RadioGroupFlex = styled(RadioGroup)`
  display: flex;
  flex-wrap: wrap;
  justify-content: space-evenly;
  padding-top: 20px;
`

export const ProgressActions = styled.div`
  display: flex;
  flex-direction: row-reverse;
  margin-top: 20px;

  button {
    margin-left: 20px;
  }
`
