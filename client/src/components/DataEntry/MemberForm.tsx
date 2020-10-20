import React from 'react'
import { H1, RadioGroup, Radio } from '@blueprintjs/core'
import { Formik, FormikProps, getIn } from 'formik'
import FormSection from '../Atoms/Form/FormSection'
import { IAuditBoardMember } from '../../types'
import FormButton from '../Atoms/Form/FormButton'
import { LabelText, NameField } from './Atoms'

interface IProps {
  boardName: string
  jurisdictionName: string
  submitMembers: (members: IAuditBoardMember[]) => void
}

const MemberForm: React.FC<IProps> = ({
  boardName,
  jurisdictionName,
  submitMembers,
}: IProps) => {
  return (
    <div>
      <H1>{boardName}: Member Sign-in</H1>
      <p>
        Enter the information below for each member of {jurisdictionName}{' '}
        {boardName} below, then click &quot;Next&quot; to proceed.
      </p>
      <Formik
        initialValues={[
          {
            name: '',
            affiliation: '',
          },
          {
            name: '',
            affiliation: '',
          },
        ]}
        onSubmit={members =>
          submitMembers(
            members
              .filter(({ name }) => name)
              .map(({ name, affiliation }) => ({
                name,
                affiliation: affiliation || null,
              }))
          )
        }
        render={({
          setFieldValue,
          values,
          handleSubmit,
        }: FormikProps<[IAuditBoardMember, IAuditBoardMember]>) => (
          <form>
            {[0, 1].map(i => (
              <FormSection label="Audit Board Member" key={i}>
                {/* eslint-disable jsx-a11y/label-has-associated-control */}
                <LabelText htmlFor={`[${i}]name`}>Full Name</LabelText>
                <NameField name={`[${i}]name`} id={`[${i}]name`} />
                <LabelText htmlFor={`[${i}]affiliation`}>
                  Party Affiliation <i>(optional)</i>
                </LabelText>
                <RadioGroup
                  name={`[${i}]affiliation`}
                  onChange={e =>
                    setFieldValue(`[${i}]affiliation`, e.currentTarget.value)
                  }
                  selectedValue={getIn(values, `[${i}]affiliation`)}
                >
                  <Radio value="DEM">Democrat</Radio>
                  <Radio value="REP">Republican</Radio>
                  <Radio value="LIB">Libertarian</Radio>
                  <Radio value="IND">Independent/Unaffiliated</Radio>
                  <Radio value="OTH">Other</Radio>
                  <Radio value="">None</Radio>
                </RadioGroup>
              </FormSection>
            ))}
            <FormButton
              intent="primary"
              type="button"
              disabled={!(values[0].name || (values[0].name && values[1].name))}
              onClick={handleSubmit}
            >
              Next
            </FormButton>
          </form>
        )}
      />
    </div>
  )
}

export default MemberForm
