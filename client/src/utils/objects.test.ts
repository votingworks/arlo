import { isObjectEmpty, isObjectEqual } from './objects'

test('isObjectEmpty', () => {
  expect(isObjectEmpty({})).toBeTruthy()
  expect(isObjectEmpty({ key: 'value' })).toBeFalsy()
})

test('isObjectEqual', () => {
  expect(isObjectEqual({}, {})).toBeTruthy()
  const a = {
    foods: {
      fruits: ['orange', 'lemon'],
    },
    numbers: {
      Decimal: {
        tens: [40, 50, 20],
        hundreds: [300, 500],
      },
      Roman: {
        small: ['I', 'VII', 'IX'],
        hundreds: [300, 500],
      },
    },
    bikes: ['recumbent', 'upright'],
  }
  const b = {
    foods: {
      fruits: ['orange', 'lemon'],
    },
    numbers: {
      Decimal: {
        tens: [40, 50, 20],
        hundreds: [300, 500],
      },
      Roman: {
        small: ['I', 'VII', 'IX'],
        hundreds: [300, 500],
      },
    },
    bikes: ['recumbent', 'upright'],
  }
  const c = {
    foods: {
      fruits: ['orange', 'lemon'],
    },
    numbers: {
      Decimal: {
        tens: [40, 50, 20],
        hundreds: [300, 700],
      },
      Roman: {
        small: ['I', 'VII', 'IX'],
        large: ['MCXVII', 'MCXXVIII', 'MMVIII'],
      },
    },
    bikes: ['recumbent', 'upright'],
  }

  expect(isObjectEqual(a, b)).toBeTruthy()
  expect(isObjectEqual(a, c)).toBeFalsy()
  expect(isObjectEqual(b, c)).toBeFalsy()
})
