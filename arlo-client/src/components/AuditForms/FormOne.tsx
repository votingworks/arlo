import React from 'react'
import styled from 'styled-components'

const Section = styled.div`
    margin 20px 0 20px 0;
`

const SectionTitle = styled.div`
    font-size: .8em;
    text-align: center; 
    margin: 40px 0 25px 0;
`
const SectionDetail = styled.div`
    font-size: .4em;
    margin-top: 10px;
`

const SectionLabel = styled.div`
    font-size: .5em;
    font-weight: bold;
`
const PageSection = styled.div`
    text-align: left;
    display: block;
    width: 50%;
`

const InputSection = styled.div`
    width: 100%;
    display: block;
    margin-top: 25px;
    font-size: .4em;
`

const TwoColumnSection = styled.div`
    width: 100%;
    display: block;
    margin-top: 25px;
    font-size: .4em;
`

const InputLabelRow = styled.div`
    width: 100%;
    display: flex; 
    flex-direction: row;
    margin-bottom: 10px;
`
const InputFieldRow = styled.div`
    width: 100%;
    display: flex; 
    flex-direction: row;
    margin-bottom: 25px;
`

const Field = styled.input`
    width: 45%;
`

const FieldRight = styled.input`
    width: 45%;
    margin-left: 50px;
`

const InputLabel = styled.label`
    display: inline-block;
`

const InputLabelRight = styled.label`
    margin-left: 75px;
`

/*const InlineInput = styled.div`
    width: 50%;
    display: flex; 
    flex-direction: row;
    justify-content: space-between;
    margin-bottom: 10px;
`*/

const ButtonBar = styled.div`
    margin 50px 0 50px 0;
    text-align: center;
`

const Button = styled.button`
    background: rgb(211,211,211);
    font-weight: bold;
    font-size: .4em;
    color: black;
    width: 200px;
    height: 30px; 
    border-radius: 5px;
    margin: 0 auto;
`

const InlineButton = styled.button`
    background: rgb(211,211,211);
    font-weight: bold;
    font-size: .4em;
    color: black;
    width: 275px;
    height: 20px; 
    border-radius: 5px;
    margin 10px 0 30px 0;
`
const InlineInput = styled.div`
    width: 50%;
    display: flex; 
    flex-direction: row;
    justify-content: space-between;
    margin-bottom: 10px;
`

const SmallInlineButton = styled.button`
    background: rgb(211,211,211);
    font-weight: bold;
    font-size: .4em;
    color: black;
    width: 170px;
    height: 20px; 
    border-radius: 5px;
    margin 10px 0 30px 0;
`

interface Props {
    formOneHasData?: any,
    audit?: any,
    generateOptions?: any,
    isLoading?: any,
    submitFormOne?: any
}

const AuditFormOne = (props: Props) => {
    const {formOneHasData, audit, generateOptions, isLoading, submitFormOne} = props
    return (
    <form id="formOne">
        <PageSection>
            <SectionTitle>Contest Information</SectionTitle>
            <Section>
                <SectionLabel>Contest Name</SectionLabel>
                <SectionDetail>Enter the name of the contest that will drive the audit.</SectionDetail>
                <Field name="name" defaultValue={formOneHasData && audit.contests[0].name} />
            </Section>
            <Section>
                <SectionLabel>Candidates/Choices & Vote Totals</SectionLabel>
                <SectionDetail>Enter the name of each candidate choice that appears on the ballot for this contest.</SectionDetail>
                <TwoColumnSection>
                    <InputLabelRow>
                        <InputLabel>Name of Candidate/Choice 1</InputLabel>
                        <InputLabelRight>Votes for Candidate/Choice 1</InputLabelRight>
                    </InputLabelRow>
                    <InputFieldRow>
                        <Field name="candidateOneName" defaultValue={formOneHasData && audit.contests[0].choices[0].name} />
                        <FieldRight type="number" name="candidateOneVotes" defaultValue={formOneHasData && audit.contests[0].choices[0].numVotes} />
                    </InputFieldRow>
                    <InputLabelRow>
                        <InputLabel>Name of Candidate/Choice 2</InputLabel>
                        <InputLabelRight>Votes for Candidate/Choice 2</InputLabelRight>
                    </InputLabelRow>
                    <InputFieldRow>
                        <Field name="candidateTwoName" defaultValue={formOneHasData && audit.contests[0].choices[1].name} />
                        <FieldRight type="number" name="candidateTwoVotes" defaultValue={formOneHasData && audit.contests[0].choices[1].numVotes} />
                    </InputFieldRow>
                </TwoColumnSection>
            </Section>
            <Section>
                <SectionLabel>Total Ballots Cast</SectionLabel>
                <SectionDetail>Enter the overall number of ballot cards cast in jurisdictoins containing this contest.</SectionDetail>
                <Field type="number" name="totalBallotsCast" defaultValue={formOneHasData && audit.contests[0].totalBallotsCast} />
            </Section>
            <SectionTitle>Audit Settings</SectionTitle>
            <Section>
                <SectionLabel>Desired Risk Limit</SectionLabel>
                <SectionDetail>Set the risk for the audit as as percentage (e.g. "5" = 5%).</SectionDetail>
                <select name="desiredRiskLimit" defaultValue={formOneHasData && audit.riskLimit}>
                    {
                        generateOptions(20)
                    }
                </select>
            </Section>
            <Section>
                <SectionLabel>Random Seed</SectionLabel>
                <SectionDetail>Enter the random number to seed the pseudo-random number generator.</SectionDetail>
                <Field type="number" defaultValue={formOneHasData && audit.randomSeed} name="randomSeed" />
            </Section>
        </PageSection>
        {!formOneHasData && isLoading &&
        <p>Loading...</p>}
        {!formOneHasData && !isLoading &&
         <ButtonBar>
           <Button onClick={e => submitFormOne(e)}>Estimate Sample Size</Button>
         </ButtonBar>
}
    </form>
    )
}

export default AuditFormOne