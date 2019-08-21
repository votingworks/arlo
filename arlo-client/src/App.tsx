import React from 'react'
import './App.css'
import styled from 'styled-components'
import { ToastContainer } from 'react-toastify'
import AuditSetupPage from './pages/AuditSetupPage'
import 'react-toastify/dist/ReactToastify.css'

const Main = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 100vh;
  padding: 40px;
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
