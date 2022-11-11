import React from 'react'
import FormButtonBar from '../../../Atoms/Form/FormButtonBar'
import FormButton from '../../../Atoms/Form/FormButton'
import FormWrapper from '../../../Atoms/Form/FormWrapper'
import { isFileProcessed } from '../../../useCSV'
import CSVFile from '../../../Atoms/CSVForm'
import { IFileUpload } from '../../../useFileUpload'
import { assert } from '../../../utilities'

interface IProps {
  goToNextStage: () => void
  jurisdictionsFileUpload: IFileUpload
  // Undefined if standardized contests file is not enabled
  standardizedContestsFileUpload?: IFileUpload
}

const Participants: React.FC<IProps> = ({
  goToNextStage,
  jurisdictionsFileUpload,
  standardizedContestsFileUpload,
}: IProps) => {
  assert(jurisdictionsFileUpload.uploadedFile.isSuccess)
  assert(
    standardizedContestsFileUpload === undefined ||
      standardizedContestsFileUpload.uploadedFile.isSuccess
  )

  const areFileUploadsComplete =
    isFileProcessed(jurisdictionsFileUpload.uploadedFile.data) &&
    (standardizedContestsFileUpload === undefined ||
      isFileProcessed(standardizedContestsFileUpload.uploadedFile.data!))

  return (
    <FormWrapper
      title={
        standardizedContestsFileUpload === undefined
          ? 'Participants'
          : 'Participants & Contests'
      }
    >
      <CSVFile
        csvFile={jurisdictionsFileUpload.uploadedFile.data}
        uploadCSVFiles={async files => {
          await jurisdictionsFileUpload.uploadFiles(files)
          return true
        }}
        title={
          standardizedContestsFileUpload !== undefined
            ? 'Participating Jurisdictions'
            : undefined
        }
        description='Click "Browse" to choose the appropriate file from your computer. This file should be a comma-separated list of all the jurisdictions participating in the audit, plus email addresses for audit administrators in each participating jurisdiction.'
        sampleFileLink="/sample_jurisdiction_filesheet.csv"
        enabled
      />
      {standardizedContestsFileUpload !== undefined && (
        <div style={{ marginTop: '30px' }}>
          <CSVFile
            csvFile={standardizedContestsFileUpload.uploadedFile.data!}
            uploadCSVFiles={async files => {
              await standardizedContestsFileUpload.uploadFiles(files)
              return true
            }}
            title="Standardized Contests"
            description='Click "Browse" to choose the appropriate file from your computer. This file should be a comma-separated list of all the contests on the ballot, the vote choices available in each, and the jurisdiction(s) where each contest appeared on the ballot.'
            sampleFileLink="/sample_standardized_contests.csv"
            enabled={isFileProcessed(jurisdictionsFileUpload.uploadedFile.data)}
          />
        </div>
      )}
      <FormButtonBar>
        <FormButton
          type="submit"
          intent="primary"
          disabled={!areFileUploadsComplete}
          onClick={goToNextStage}
        >
          Next
        </FormButton>
      </FormButtonBar>
    </FormWrapper>
  )
}

export default Participants
