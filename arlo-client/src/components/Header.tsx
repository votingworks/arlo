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

const Header = () => {

    return (
        <HeaderContainer>
           ARLO
           <ButtonBar>
                <Button>Clear & Restart</Button>
           </ButtonBar>
        </HeaderContainer>
    );

}

export default Header