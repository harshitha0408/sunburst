const AUTO_REPLY_LABEL = "AutoReplied";
const MAX_EMAILS_PER_RUN = 100;

function autoReplyToUnrespondedEmails() {
  const label = getOrCreateLabel(AUTO_REPLY_LABEL);
  const threads = GmailApp.search(
    'is:inbox -label:' + AUTO_REPLY_LABEL + ' newer_than:7d',
    0,
    500 // Fetch up to 500 threads to prioritize newest
  );

  // Sort threads by most recent activity (descending)
  threads.sort((a, b) => b.getLastMessageDate() - a.getLastMessageDate());

  let count = 0;

  for (let i = 0; i < threads.length && count < MAX_EMAILS_PER_RUN; i++) {
    const thread = threads[i];
    const messages = thread.getMessages();
    const lastMessage = messages[messages.length - 1];

    if (threadHasUserReply(messages)) continue;
    if (isBounceEmail(lastMessage.getFrom())) continue;

    GmailApp.sendEmail(
      lastMessage.getFrom(),
      "Thank you for contacting us",
`Dear ${getNameFromEmail(lastMessage.getFrom())},

Thank you for reaching out to us. We’ve received your message and our team will get back to you shortly.

We appreciate your patience.

Best regards,  
[Your Company Name]
[Your Contact Info / Website]`
    );

    thread.addLabel(label);
    count++;
  }
}

function getOrCreateLabel(name) {
  let label = GmailApp.getUserLabelByName(name);
  if (!label) {
    label = GmailApp.createLabel(name);
  }
  return label;
}

function threadHasUserReply(messages) {
  for (let i = 1; i < messages.length; i++) {
    if (messages[i].isDraft()) continue;
    if (messages[i].getFrom().includes(Session.getActiveUser().getEmail())) {
      return true;
    }
  }
  return false;
}

function isBounceEmail(fromAddress) {
  const lowerFrom = fromAddress.toLowerCase();
  return (
    lowerFrom.includes("mailer-daemon") ||
    lowerFrom.includes("postmaster") ||
    lowerFrom.includes("bounce") ||
    lowerFrom.includes("noreply") ||
    lowerFrom.includes("do-not-reply")
  );
}

function getNameFromEmail(email) {
  const match = email.match(/^(.*?)(<.*?>)?$/);
  return match && match[1].trim() ? match[1].trim() : "there";
}
