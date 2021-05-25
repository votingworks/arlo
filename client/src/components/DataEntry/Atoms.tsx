import styled from 'styled-components'
import { Field } from 'formik'
import { RadioGroup, Divider, H5, Colors } from '@blueprintjs/core'

export const FlushDivider = styled(Divider)`
  margin: 5px 0;
`

export const BallotRow = styled.div`
  display: flex;
  justify-content: flex-start;
  margin: 25px 0;

  .ballot-main {
    width: 100%;

    .bp3-button {
      text-align: center;
    }
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

export const ContestCard = styled.div`
  margin: 20px 0;
  background-color: #ced9e0;
  padding: 20px;

  &:first-child {
    margin-top: 10px;
  }
`

export const RadioGroupFlex = styled(RadioGroup)`
  display: flex;
  flex-wrap: wrap;
  justify-content: start;
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

export const LabelText = styled.label`
  display: block;
  margin: 5px 0;
`

export const NameField = styled(Field)`
  margin-bottom: 20px;
  width: 300px;
`

export const BlockCheckboxes = styled.div`
  display: flex;
  justify-content: space-between;
  @media only screen and (max-width: 767px) {
    flex-direction: column;
  }
`

export const LeftCheckboxes = styled.div`
  display: flex;
  flex-direction: column;
  width: 50%;
  @media only screen and (max-width: 767px) {
    width: 100%;
  }
`

export const RightCheckboxes = styled.div`
  width: 25%;
  @media only screen and (max-width: 767px) {
    margin-top: 20px;
    width: 100%;
  }
`

export const SubTitle = styled(H5)`
  margin-bottom: 0;
  color: ${Colors.BLACK};
  font-weight: 400;
`
