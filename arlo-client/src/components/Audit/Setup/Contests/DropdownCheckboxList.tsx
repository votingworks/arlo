import React from 'react'
import styled from 'styled-components'
import { FormikProps, getIn } from 'formik'
import { Popover, Position, Menu, Checkbox } from '@blueprintjs/core'
import FormButton from '../../../Atoms/Form/FormButton'
import { IContest } from '../../../../types'

const CustomMenuItem = styled.li`
  .bp3-menu-item {
    display: inline-block;
    width: 100%;
  }
  .bp3-checkbox {
    float: right;
    margin: 0;
  }
`

export type ICheckboxList = {
  title: string
  value: string
  checked: boolean
}[]

interface IProps {
  formikBag: {
    values: FormikProps<IContest[]>['values']
    setFieldValue: FormikProps<IContest[]>['setFieldValue']
  }
  text: string
  optionList: ICheckboxList
  contestIndex: number
}

const DropdownCheckboxList = ({
  formikBag: { values, setFieldValue },
  text,
  optionList,
  contestIndex,
}: IProps) => {
  const jurisdictionList = getIn(
    values,
    `contests[${contestIndex}].jurisdictionIds`
  )
  const updateList = (value: string, checked: boolean) => {
    const itemIndex = jurisdictionList.indexOf(value)
    /* istanbul ignore else */
    if (checked && itemIndex === -1) {
      jurisdictionList.push(value)
    } else if (!checked && itemIndex > -1) {
      jurisdictionList.splice(itemIndex, 1)
    }
    setFieldValue(`contests[${contestIndex}].jurisdictionIds`, jurisdictionList)
  }
  const menu = (
    <Menu>
      {optionList.map(v => (
        <CustomMenuItem key={v.value}>
          {/* eslint-disable-next-line jsx-a11y/label-has-associated-control */}
          <label className="bp3-menu-item">
            {v.title}
            <Checkbox
              inline
              checked={jurisdictionList.indexOf(v.value) > -1}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                updateList(v.value, e.currentTarget.checked)
              }
            />
          </label>
        </CustomMenuItem>
      ))}
    </Menu>
  )
  return (
    <Popover position={Position.BOTTOM} content={menu}>
      <FormButton>{text}</FormButton>
    </Popover>
  )
}

export default DropdownCheckboxList
