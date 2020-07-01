import jsPDF from 'jspdf'
import { IBallot } from '../../../types'
import { IAuditBoard } from '../useAuditBoards'

export const downloadLabels = async (
  roundNum: number,
  ballots: IBallot[]
): Promise<void> => {
  /* istanbul ignore else */
  if (ballots.length) {
    const getX = (l: number): number => (l % 3) * 60 + 9 * ((l % 3) + 1)
    const getY = (l: number): number[] => [
      Math.floor(l / 3) * 25.5 + 20,
      Math.floor(l / 3) * 25.5 + 25,
      Math.floor(l / 3) * 25.5 + 34,
    ]
    const labels = new jsPDF({ format: 'letter' })
    labels.setFontSize(9)
    let labelCount = 0
    ballots.forEach(ballot => {
      labelCount += 1
      if (labelCount > 30) {
        labels.addPage('letter')
        labelCount = 1
      }
      const x = getX(labelCount - 1)
      const y = getY(labelCount - 1)
      labels.text(
        labels.splitTextToSize(ballot.auditBoard!.name, 60)[0],
        x,
        y[0]
      )
      labels.text(
        labels.splitTextToSize(`Batch Name: ${ballot.batch.name}`, 60),
        x,
        y[1]
      )
      labels.text(`Ballot Number: ${ballot.position}`, x, y[2])
    })
    labels.autoPrint()
    labels.save(`Round ${roundNum} Labels.pdf`)
  }
}

export const downloadPlaceholders = async (
  roundNum: number,
  ballots: IBallot[]
): Promise<void> => {
  /* istanbul ignore else */
  if (ballots.length) {
    const placeholders = new jsPDF({ format: 'letter' })
    placeholders.setFontSize(20)
    let pageCount = 0
    ballots.forEach(ballot => {
      if (pageCount > 0) placeholders.addPage('letter')
      placeholders.text(
        placeholders.splitTextToSize(ballot.auditBoard!.name, 180),
        20,
        20
      )
      placeholders.text(
        placeholders.splitTextToSize(`Batch Name: ${ballot.batch.name}`, 180),
        20,
        40
      )
      placeholders.text(`Ballot Number: ${ballot.position}`, 20, 100)
      pageCount += 1
    })
    placeholders.autoPrint()
    placeholders.save(`Round ${roundNum} Placeholders.pdf`)
  }
}

export const downloadDataEntry = (auditBoards: IAuditBoard[]): string => {
  const auditBoardsWithoutBallots: string[] = []
  const auditBoardCreds = new jsPDF({ format: 'letter' })
  auditBoards.forEach((board, i) => {
    const qr: HTMLCanvasElement | null = document.querySelector(
      `#qr-${board.passphrase} > canvas`
    )
    if (qr && board.currentRoundStatus.numSampledBallots > 0) {
      if (i > 0) auditBoardCreds.addPage('letter')
      const url = qr.toDataURL()
      auditBoardCreds.setFontSize(22)
      auditBoardCreds.setFontStyle('bold')
      auditBoardCreds.text(board.name, 20, 20)
      auditBoardCreds.setFontSize(14)
      auditBoardCreds.setFontStyle('normal')
      auditBoardCreds.text(
        'Scan this QR code to enter the votes you see on your assigned ballots.',
        20,
        40
      )
      auditBoardCreds.addImage(url, 'JPEG', 20, 50, 50, 50)
      auditBoardCreds.text(
        auditBoardCreds.splitTextToSize(
          'If you are not able to scan the QR code, you may also type the following URL into a web browser to access the data entry portal.',
          180
        ),
        20,
        120
      )
      auditBoardCreds.text(
        `${window.location.origin}/auditboard/${board.passphrase}`,
        20,
        140
      )
    } else if (board.currentRoundStatus.numSampledBallots === 0) {
      auditBoardsWithoutBallots.push(board.name)
    }
  })
  if (auditBoardsWithoutBallots.length) {
    auditBoardCreds.addPage('letter')
    auditBoardsWithoutBallots.forEach((name, i) => {
      auditBoardCreds.text(`${name}: No ballots`, 20, i * 10 + 20)
    })
  }
  auditBoardCreds.autoPrint()
  auditBoardCreds.save(`Audit Boards Credentials for Data Entry.pdf`)
  return auditBoardCreds.output()
}
