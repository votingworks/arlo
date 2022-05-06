import React from 'react'
import { Page, StyleSheet, Text, View } from '@react-pdf/renderer'

import { blankLine } from '../../../utils/string'
import { ICandidate } from '../../../types'
import {
  PdfCheckbox,
  PdfDividerLine,
  PdfSignatureLine,
  PdfTable,
  PdfTd,
  PdfTr,
} from '../../Atoms/pdf'

const styles = StyleSheet.create({
  page: {
    fontFamily: 'Helvetica', // @react-pdf comes pre-packaged with this font
    fontSize: 12,
    padding: 36,
  },
  pageSection: {
    marginBottom: 24,
  },
  heading: {
    fontSize: 18,
  },
  subHeading: {
    fontSize: 16,
    marginTop: 10,
  },
  p: {
    marginBottom: 10,
    overflow: 'hidden',
  },
  pLastInSection: {
    marginBottom: 0,
    overflow: 'hidden',
  },
  bold: {
    fontFamily: 'Helvetica-Bold', // @react-pdf comes pre-packaged with this font
  },
  flexRow: {
    display: 'flex',
    flexDirection: 'row',
  },
  overflowHidden: {
    overflow: 'hidden',
  },
})

interface IProps {
  auditBoardName: string
  batchName: string
  choices: ICandidate[]
  jurisdictionName: string
}

const BatchTallySheet = ({
  auditBoardName,
  batchName,
  choices,
  jurisdictionName,
}: IProps): JSX.Element => {
  return (
    <Page style={styles.page} size="LETTER">
      <View style={styles.pageSection}>
        <Text style={styles.heading}>Audit Board Batch Tally Sheet</Text>
        <Text style={styles.subHeading}>
          Batch Name: <Text style={styles.bold}>{batchName}</Text>
        </Text>
      </View>
      <View style={styles.pageSection}>
        <Text style={styles.p}>Jurisdiction: {jurisdictionName}</Text>
        <Text style={styles.p}>Audit Board: {auditBoardName}</Text>
        <Text style={styles.pLastInSection}>
          Batch Type (Optional): {blankLine(20)}
        </Text>
      </View>
      <View style={styles.pageSection}>
        <PdfCheckbox
          fontSize={styles.page.fontSize}
          textBeforeCheckbox="Was the container sealed when received by the audit board?"
          textAfterCheckbox="Yes"
        />
      </View>
      <View style={styles.pageSection}>
        <PdfTable>
          <PdfTr>
            <PdfTd>
              <Text style={styles.bold}>Candidates/Choices</Text>
            </PdfTd>
            <PdfTd>
              <Text style={styles.bold}>Enter Stack Totals</Text>
            </PdfTd>
          </PdfTr>
          {choices.map(c => (
            <PdfTr key={c.id}>
              <PdfTd>
                <Text style={styles.overflowHidden}>{c.name}</Text>
              </PdfTd>
              {/* Blank, to be filled in by audit board */}
              <PdfTd />
            </PdfTr>
          ))}
        </PdfTable>
      </View>
      <View style={styles.pageSection}>
        <Text style={styles.p}>
          When work is completed, return all ballots to the ballot container and
          seal the container.
        </Text>
        <PdfCheckbox
          fontSize={styles.page.fontSize}
          textBeforeCheckbox="Was the container resealed by the audit board?"
          textAfterCheckbox="Yes"
        />
      </View>
      <View style={[styles.pageSection, styles.flexRow]}>
        <PdfSignatureLine label="(Audit Board Member)" marginRight={9} />
        <PdfSignatureLine label="(Audit Board Member)" />
      </View>
      <View style={styles.pageSection}>
        <PdfDividerLine />
      </View>
      <View style={styles.pageSection}>
        <Text style={[styles.p, styles.bold]}>Check-In/Out Station Steps:</Text>
        <PdfCheckbox
          fontSize={styles.page.fontSize}
          marginBottom={styles.p.marginBottom}
          textAfterCheckbox="Recorded batch check-in"
        />
        <PdfCheckbox
          fontSize={styles.page.fontSize}
          marginBottom={styles.p.marginBottom}
          textAfterCheckbox="Entered tallies into Arlo"
        />
        <Text style={styles.pLastInSection}>
          {blankLine(5)} Initials of check-in/out station member
        </Text>
      </View>
    </Page>
  )
}

export default BatchTallySheet
