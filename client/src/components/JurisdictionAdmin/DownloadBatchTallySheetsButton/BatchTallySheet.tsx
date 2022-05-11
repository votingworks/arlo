import React, { ReactNode } from 'react'
import { Page, StyleSheet, Text, View } from '@react-pdf/renderer'
import { Style } from '@react-pdf/types'

import { blankLine } from '../../../utils/string'
import { ICandidate } from '../../../types'
import {
  PdfCheckbox,
  PdfDividerLine,
  PdfP,
  PdfHeading,
  PdfSignatureLine,
  PdfSubHeading,
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
  withSmallBottomMargin: {
    marginBottom: 10,
  },
})

interface IPageSectionProps {
  children: ReactNode
  style?: Style
}

const PageSection = ({ children, style }: IPageSectionProps): JSX.Element => {
  return (
    <View
      style={{
        ...styles.pageSection,
        ...style,
      }}
    >
      {children}
    </View>
  )
}

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
      <PageSection>
        <PdfHeading>Audit Board Batch Tally Sheet</PdfHeading>
        <PdfSubHeading>
          Batch Name: <Text style={styles.bold}>{batchName}</Text>
        </PdfSubHeading>
      </PageSection>

      <PageSection>
        <PdfP>Jurisdiction: {jurisdictionName}</PdfP>
        <PdfP>Audit Board: {auditBoardName}</PdfP>
        <PdfP lastInSection>Batch Type (Optional): {blankLine(20)}</PdfP>
      </PageSection>

      <PageSection style={styles.flexRow}>
        <Text>
          Was the container sealed when received by the audit board?&nbsp;&nbsp;
        </Text>
        <PdfCheckbox fontSize={styles.page.fontSize} />
        <Text>&nbsp;Yes</Text>
      </PageSection>

      <PageSection>
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
      </PageSection>

      <PageSection>
        <PdfP>
          When work is completed, return all ballots to the ballot container and
          seal the container.
        </PdfP>
        <View style={styles.flexRow}>
          <Text>
            Was the container resealed by the audit board?&nbsp;&nbsp;
          </Text>
          <PdfCheckbox fontSize={styles.page.fontSize} />
          <Text>&nbsp;Yes</Text>
        </View>
      </PageSection>

      <PageSection style={styles.flexRow}>
        <PdfSignatureLine
          label="(Audit Board Member)"
          style={{ marginRight: 10 }}
        />
        <PdfSignatureLine label="(Audit Board Member)" />
      </PageSection>

      <PageSection>
        <PdfDividerLine />
      </PageSection>

      <PageSection>
        <PdfP style={styles.bold}>Check-In/Out Station Steps:</PdfP>
        <View style={[styles.flexRow, styles.withSmallBottomMargin]}>
          <PdfCheckbox fontSize={styles.page.fontSize} />
          <Text>&nbsp;Recorded batch check-in</Text>
        </View>
        <View style={[styles.flexRow, styles.withSmallBottomMargin]}>
          <PdfCheckbox fontSize={styles.page.fontSize} />
          <Text>&nbsp;Entered tallies into Arlo</Text>
        </View>
        <PdfP lastInSection>
          {blankLine(5)} Initials of check-in/out station member
        </PdfP>
      </PageSection>
    </Page>
  )
}

export default BatchTallySheet
