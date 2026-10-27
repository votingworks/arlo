import * as Yup from 'yup'
import number from '../../../../utils/number-schema'
import {
  RANDOM_SEED_MAX_LENGTH,
  RANDOM_SEED_MAX_LENGTH_ERROR,
} from '../../RandomSeedModal'

const schema = Yup.object().shape({
  state: Yup.string().required('Required'),
  electionName: Yup.string().required('Required'),
  randomSeed: Yup.string()
    .max(RANDOM_SEED_MAX_LENGTH, RANDOM_SEED_MAX_LENGTH_ERROR)
    .required('Required'),
  riskLimit: number()
    .typeError('Must be a number')
    .min(1, 'Must be greater than 0')
    .max(20, 'Must be less than 21')
    .required('Required'),
})

export default schema
