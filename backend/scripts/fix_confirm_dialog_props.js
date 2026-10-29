const fs = require('fs');
const file = 'frontend/src/components/damage/DamageReport.tsx';
let content = fs.readFileSync(file, 'utf8');

const target = `<ConfirmationDialog
        isOpen={showNoDamageConfirm}
        title="Confirm Return & Close Agreement?"
        message="You are confirming that you do not wish to report damage for this return. This will record your decision and begin the agreement closure process. Please verify the return evidence and outstanding obligations before proceeding."
        confirmLabel="Confirm and Close Agreement"
        cancelLabel="Cancel"
        isLoading={ownerDecisionMutation.isPending}
        onConfirm={() => {
          setShowNoDamageConfirm(false)
          ownerDecisionMutation.mutate({ decision: "NO_DAMAGE_REPORTED" })
        }}
        onCancel={() => setShowNoDamageConfirm(false)}
      />`;

const replacement = `<ConfirmationDialog
        isOpen={showNoDamageConfirm}
        title="Confirm Return & Close Agreement?"
        description="You are confirming that you do not wish to report damage for this return. This will record your decision and begin the agreement closure process. Please verify the return evidence and outstanding obligations before proceeding."
        confirmText="Confirm and Close Agreement"
        cancelText="Cancel"
        loading={ownerDecisionMutation.isPending}
        onConfirm={() => {
          setShowNoDamageConfirm(false)
          ownerDecisionMutation.mutate({ decision: "NO_DAMAGE_REPORTED" })
        }}
        onCancel={() => setShowNoDamageConfirm(false)}
      />`;

if (content.includes(target)) {
  content = content.replace(target, replacement);
  fs.writeFileSync(file, content, 'utf8');
  console.log('Fixed ConfirmationDialog props in DamageReport.tsx');
} else {
  console.log('Target not found');
}

