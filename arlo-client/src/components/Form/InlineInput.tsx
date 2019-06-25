import React from 'react'
import styled from 'styled-components'

const InputContainer = styled.div`
    width: 50%;
    display: flex; 
    flex-direction: row;
    justify-content: space-between;
    margin-bottom: 10px;
`

const InputLabel = styled.label`
    display: inline-block;
`

interface Props {
    label?: String,
    value?: any,
    onChange?: any,
    name?: any,
    defaultValue?: any
}

const InlineInput = (props: Props) => {
    const {label, value, onChange, ...restProps} = props
    return (
        <InputContainer>
            <InputLabel>{label}</InputLabel>
            <input value={value} onChange={onChange} {...restProps}/>
        </InputContainer>
    )
}

export default InlineInput