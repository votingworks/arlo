import React from 'react'
import styled from 'styled-components';


const HeaderContainer = styled.div`
    text-align: center;
    height 100px;
    padding: 20px;
`
const ButtonBar = styled.div `
    display: inline-block;
    float: right;
`

const Button = styled.button`
    background: rgb(211,211,211);
    font-weight: bold;
    font-size: .4em;
    color: black;
    width: 155px;
    height: 30px; 
    border-radius: 5px;
    margin: 0 auto;
`

// TODO: refactor so we're not copying code here from AuditForms.tsx
// doing this for now so there are fewer merge conflicts later.
function api<T>(endpoint: string, options: any): Promise<T> {
    console.log("options: ", options)
    return fetch(endpoint, options)
        .then(res => {
            if (!res.ok) {
                throw new Error(res.statusText)
            }
            return res.json() as Promise<T>
        })
}



const Header = () => {

  const reset = async () => {
    await api(`/audit/reset`, {method: "POST"});
  }
  
  return (
    <HeaderContainer>
      ARLO
      <ButtonBar>
        <Button onClick={reset}>Clear & Restart</Button>
      </ButtonBar>
    </HeaderContainer>
  );
  
}

export default Header
