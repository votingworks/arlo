import React from 'react'
import './App.css'
import styled from 'styled-components'
import { ToastContainer } from 'react-toastify'
import AuditSetupPage from './pages/AuditSetupPage'
import 'react-toastify/dist/ReactToastify.css'

const Main = styled.div`
  display: block;
  margin: auto;
  max-width: 35rem;
  height: 100%;
  overflow: scroll;
  font-size: 1.25rem;
`

const App: React.FC = () => {
  return (
    <>
      <ToastContainer />
      <Main>
        <AuditSetupPage></AuditSetupPage>
      </Main>
    </>
  )
}

export default App
