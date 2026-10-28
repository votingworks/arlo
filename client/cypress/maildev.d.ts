declare module 'maildev' {
  namespace MailDev {
    interface Options {
      ip?: string
      smtp?: number | string
      incomingUser?: string
      incomingPass?: string
      disableWeb?: boolean
    }

    interface Email {
      headers: Record<string, string>
    }
  }

  class MailDev {
    constructor(options?: MailDev.Options)
    listen(callback?: (error?: Error) => void): void
    on(event: 'new', listener: (email: MailDev.Email) => void): this
  }

  export = MailDev
}
