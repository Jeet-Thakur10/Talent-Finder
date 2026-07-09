def get_generic_email_html(
    title: str,
    body: str,
    action_text: str | None = None,
    action_url: str | None = None,
) -> str:
    """Generates a clean, client-compatible, responsive HTML email body.

    Suitable for Gmail, Outlook, Apple Mail, and mobile clients.
    """
    action_button_html = ""
    if action_text and action_url:
        action_button_html = f"""
        <table border="0" cellpadding="0" cellspacing="0" style="margin: 0 auto 10px 0;">
          <tr>
            <td align="left" style="border-radius: 8px; background-color: #0f172a;">
              <a href="{action_url}" target="_blank" style="display: inline-block; padding: 14px 24px; font-size: 14px; font-weight: 600; color: #ffffff; text-decoration: none; border-radius: 8px; border: 1px solid #0f172a;">{action_text}</a>
            </td>
          </tr>
        </table>
        """

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;">
  <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f8fafc; padding: 40px 20px;">
    <tr>
      <td align="center">
        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
          <!-- Header (Branding) -->
          <tr>
            <td style="padding: 32px 40px; background-color: #0f172a; text-align: left;">
              <span style="font-size: 20px; font-weight: bold; color: #ffffff; letter-spacing: -0.5px;">Talent Finder</span>
            </td>
          </tr>
          <!-- Body Content -->
          <tr>
            <td style="padding: 40px 40px 32px 40px;">
              <h1 style="margin: 0 0 20px 0; font-size: 22px; font-weight: 700; color: #0f172a; line-height: 1.3;">{title}</h1>
              <p style="margin: 0 0 30px 0; font-size: 16px; line-height: 1.6; color: #334155;">{body}</p>
              {action_button_html}
            </td>
          </tr>
          <!-- Divider -->
          <tr>
            <td style="padding: 0 40px;">
              <table border="0" cellpadding="0" cellspacing="0" width="100%" style="border-top: 1px solid #f1f5f9;">
                <tr><td></td></tr>
              </table>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="padding: 32px 40px; text-align: left;">
              <p style="margin: 0 0 8px 0; font-size: 12px; line-height: 1.5; color: #64748b;">
                This email was sent by Talent Finder. Please do not reply directly to this message.
              </p>
              <p style="margin: 0; font-size: 12px; line-height: 1.5; color: #94a3b8;">
                &copy; 2026 Talent Finder. All rights reserved.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def get_welcome_email_html(
    name: str,
    email: str,
    password: str,
    login_url: str,
) -> str:
    body = (
        f"Hello {name},<br/><br/>"
        "Your recruiter account has been created.<br/><br/>"
        "You can now log in to Talent Finder using:<br/><br/>"
        "Email:<br/>"
        f"{email}<br/><br/>"
        "Password:<br/>"
        f"{password}<br/><br/>"
        "Login URL:<br/>"
        f"{login_url}<br/><br/>"
        "Please change your password after your first login if required.<br/><br/>"
        "Regards,<br/>"
        "Talent Finder"
    )
    return get_generic_email_html(
        title="Welcome to Talent Finder",
        body=body,
    )

