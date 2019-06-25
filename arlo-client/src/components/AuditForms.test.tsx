import React from 'react';
import { render } from '@testing-library/react'
import AuditForms from './AuditForms/AuditForms';

it('renders corretly', () => {
    const { container } = render(<AuditForms />)
    expect(container).toMatchSnapshot()
});
