import React from 'react'
import { FormikProps, getIn } from 'formik'
import { Popover, Position, Menu, Checkbox } from '@blueprintjs/core'
import FormButton from './FormButton'

interface IValues {
  jurisdictionIds: {
    title: string
    value: string
    checked: boolean
  }[]
}

interface IProps {
  formikBag: FormikProps<IValues>
  text: string
}

const DropdownCheckboxList = ({
  formikBag: { values, setFieldValue },
  text,
}: IProps) => {
  const menu = (
    <Menu>
      {values.jurisdictionIds.map((v, i) => (
        <Menu.Item text={v.title} key={v.value} shouldDismissPopover={false}>
          <Checkbox
            checked={getIn(values, `jurisdictionIds[${i}].checked`)}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setFieldValue(
                `jurisdictionIds[${i}].checked`,
                e.currentTarget.value
              )
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
