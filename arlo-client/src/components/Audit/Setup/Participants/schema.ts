import * as Yup from 'yup'

const participantsSchema = Yup.object().shape({
  state: Yup.string().required('Required'),
})

export default participantsSchema
