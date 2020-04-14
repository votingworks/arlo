import React from 'react'
import { FormikProps, getIn } from 'formik'
import { Popover, Position, Menu, Checkbox } from '@blueprintjs/core'
import FormButton from '../../../Atoms/Form/FormButton'
import { IContests } from './types'

export type ICheckboxList = {
  title: string
  value: string
  checked: boolean
}[]

interface IProps {
  formikBag: {
    values: FormikProps<IContests>['values']
    setFieldValue: FormikProps<IContests>['setFieldValue']
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
        <Menu.Item text={v.title} key={v.value} shouldDismissPopover={false}>
          <Checkbox
            checked={jurisdictionList.indexOf(v.value) > -1}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              updateList(v.value, e.currentTarget.checked)
            }
          />
        </Menu.Item>
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
