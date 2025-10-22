"""Strategy Approval Workflow (T090-T092).

Implements human-in-the-loop approval for automated recommendations:
- User reviews automated recommendations
- User can APPROVE, REJECT, or REQUEST_REVISION
- Only APPROVED recommendations trigger actual trades
- Audit trail: who approved, when, why
- Prevents rogue automated trades

Workflow States:
1. PENDING_APPROVAL: Automated rec waiting for review
2. APPROVED: User approved → ready to execute
3. REJECTED: User rejected → do not trade
4. REQUEST_REVISION: User wants changes → back to strategy team
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from investlib_data.models import StrategyApproval, ApprovalStatus, InvestmentRecommendation


logger = logging.getLogger(__name__)


class ApprovalWorkflow:
    """Manages approval workflow for automated recommendations."""

    def __init__(self, session: Session):
        """Initialize approval workflow.

        Args:
            session: Database session
        """
        self.session = session

    def submit_for_approval(
        self,
        recommendation_id: int,
        submitted_by: str = "scheduler"
    ) -> StrategyApproval:
        """Submit recommendation for approval.

        Args:
            recommendation_id: ID of InvestmentRecommendation
            submitted_by: Who submitted (default: "scheduler" for automated)

        Returns:
            StrategyApproval record

        Raises:
            ValueError: If recommendation doesn't exist or already has approval
        """
        # Validate recommendation exists
        rec = self.session.query(InvestmentRecommendation).filter_by(id=recommendation_id).first()
        if not rec:
            raise ValueError(f"Recommendation {recommendation_id} not found")

        # Check if already has approval
        existing = self.session.query(StrategyApproval).filter_by(
            recommendation_id=recommendation_id
        ).first()
        if existing:
            logger.warning(f"[Approval] Recommendation {recommendation_id} already has approval record")
            return existing

        # Create approval request
        approval = StrategyApproval(
            recommendation_id=recommendation_id,
            status=ApprovalStatus.PENDING_APPROVAL,
            submitted_by=submitted_by,
            submitted_at=datetime.now(),
            risk_level=rec.risk_level or "MEDIUM",
            expected_return_pct=(rec.take_profit - rec.entry_price) / rec.entry_price * 100 if rec.take_profit and rec.entry_price else 0,
            max_loss_pct=rec.max_loss_pct or 2.5,
            notes=f"Automated submission from {submitted_by}"
        )
        self.session.add(approval)
        self.session.commit()

        logger.info(f"[Approval] ✅ Submitted recommendation {recommendation_id} for approval")
        return approval

    def approve(
        self,
        approval_id: int,
        approved_by: str,
        approval_notes: Optional[str] = None
    ) -> StrategyApproval:
        """Approve a recommendation.

        Args:
            approval_id: ID of StrategyApproval
            approved_by: User who approved
            approval_notes: Optional notes

        Returns:
            Updated StrategyApproval

        Raises:
            ValueError: If approval not found or invalid state
        """
        approval = self.session.query(StrategyApproval).filter_by(id=approval_id).first()
        if not approval:
            raise ValueError(f"Approval {approval_id} not found")

        if approval.status != ApprovalStatus.PENDING_APPROVAL:
            raise ValueError(f"Cannot approve: status is {approval.status}, not PENDING_APPROVAL")

        approval.status = ApprovalStatus.APPROVED
        approval.approved_by = approved_by
        approval.approved_at = datetime.now()
        approval.notes = approval_notes or "Approved"

        self.session.commit()

        logger.info(f"[Approval] ✅ APPROVED by {approved_by}: {approval.recommendation_id}")
        return approval

    def reject(
        self,
        approval_id: int,
        rejected_by: str,
        rejection_reason: str
    ) -> StrategyApproval:
        """Reject a recommendation.

        Args:
            approval_id: ID of StrategyApproval
            rejected_by: User who rejected
            rejection_reason: Reason for rejection

        Returns:
            Updated StrategyApproval

        Raises:
            ValueError: If approval not found or invalid state
        """
        approval = self.session.query(StrategyApproval).filter_by(id=approval_id).first()
        if not approval:
            raise ValueError(f"Approval {approval_id} not found")

        if approval.status not in [ApprovalStatus.PENDING_APPROVAL, ApprovalStatus.REQUEST_REVISION]:
            raise ValueError(f"Cannot reject: status is {approval.status}")

        approval.status = ApprovalStatus.REJECTED
        approval.approved_by = rejected_by  # Store who made decision
        approval.approved_at = datetime.now()
        approval.notes = f"REJECTED: {rejection_reason}"

        self.session.commit()

        logger.info(f"[Approval] ❌ REJECTED by {rejected_by}: {approval.recommendation_id} - {rejection_reason}")
        return approval

    def request_revision(
        self,
        approval_id: int,
        requested_by: str,
        revision_notes: str
    ) -> StrategyApproval:
        """Request revision of a recommendation.

        Args:
            approval_id: ID of StrategyApproval
            requested_by: User requesting revision
            revision_notes: What needs to be revised

        Returns:
            Updated StrategyApproval

        Raises:
            ValueError: If approval not found or invalid state
        """
        approval = self.session.query(StrategyApproval).filter_by(id=approval_id).first()
        if not approval:
            raise ValueError(f"Approval {approval_id} not found")

        if approval.status != ApprovalStatus.PENDING_APPROVAL:
            raise ValueError(f"Cannot request revision: status is {approval.status}")

        approval.status = ApprovalStatus.REQUEST_REVISION
        approval.notes = f"REVISION REQUESTED by {requested_by}: {revision_notes}"

        self.session.commit()

        logger.info(f"[Approval] 🔄 REVISION REQUESTED by {requested_by}: {approval.recommendation_id}")
        return approval

    def get_pending_approvals(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all pending approvals.

        Args:
            limit: Maximum number of results

        Returns:
            List of pending approval dicts with recommendation details
        """
        approvals = self.session.query(StrategyApproval).filter_by(
            status=ApprovalStatus.PENDING_APPROVAL
        ).order_by(StrategyApproval.submitted_at.desc()).limit(limit).all()

        results = []
        for approval in approvals:
            rec = approval.recommendation
            results.append({
                'approval_id': approval.id,
                'recommendation_id': approval.recommendation_id,
                'symbol': rec.symbol,
                'action': rec.action,
                'confidence': rec.confidence,
                'entry_price': rec.entry_price,
                'position_size_pct': rec.position_size_pct,
                'risk_level': approval.risk_level,
                'expected_return_pct': approval.expected_return_pct,
                'max_loss_pct': approval.max_loss_pct,
                'submitted_by': approval.submitted_by,
                'submitted_at': approval.submitted_at,
                'data_source': rec.data_source,
                'data_freshness': rec.data_freshness
            })

        return results

    def get_approval_stats(self) -> Dict[str, int]:
        """Get approval statistics.

        Returns:
            Dict with counts by status
        """
        stats = {}
        for status in ApprovalStatus:
            count = self.session.query(StrategyApproval).filter_by(status=status).count()
            stats[status.value] = count

        return stats


def create_approval_ui_component():
    """Streamlit UI component for approval workflow (T093).

    This would be used in investapp dashboard to show pending approvals.
    """
    import streamlit as st
    from investlib_data.database import SessionLocal

    st.subheader("📋 Strategy Approval Queue")

    session = SessionLocal()
    workflow = ApprovalWorkflow(session)

    # Get pending approvals
    pending = workflow.get_pending_approvals()

    if not pending:
        st.info("✅ No pending approvals")
        return

    st.write(f"**{len(pending)} recommendations awaiting approval**")

    for item in pending:
        with st.expander(f"{item['symbol']} - {item['action']} ({item['confidence']})"):
            col1, col2 = st.columns(2)

            with col1:
                st.metric("Entry Price", f"¥{item['entry_price']:.2f}")
                st.metric("Position Size", f"{item['position_size_pct']:.1f}%")
                st.metric("Risk Level", item['risk_level'])

            with col2:
                st.metric("Expected Return", f"+{item['expected_return_pct']:.1f}%")
                st.metric("Max Loss", f"-{item['max_loss_pct']:.1f}%")
                st.metric("Data Source", item['data_source'])

            st.caption(f"Submitted by: {item['submitted_by']} at {item['submitted_at']}")

            # Action buttons
            col_approve, col_reject, col_revise = st.columns(3)

            with col_approve:
                if st.button("✅ Approve", key=f"approve_{item['approval_id']}"):
                    workflow.approve(
                        item['approval_id'],
                        approved_by="user",  # TODO: Get from session
                        approval_notes="Approved via dashboard"
                    )
                    st.success("Approved!")
                    st.rerun()

            with col_reject:
                if st.button("❌ Reject", key=f"reject_{item['approval_id']}"):
                    reason = st.text_input("Rejection reason:", key=f"reason_{item['approval_id']}")
                    if reason:
                        workflow.reject(item['approval_id'], "user", reason)
                        st.error("Rejected")
                        st.rerun()

            with col_revise:
                if st.button("🔄 Request Revision", key=f"revise_{item['approval_id']}"):
                    notes = st.text_input("Revision notes:", key=f"notes_{item['approval_id']}")
                    if notes:
                        workflow.request_revision(item['approval_id'], "user", notes)
                        st.warning("Revision requested")
                        st.rerun()

    session.close()


    # Show approval stats
    st.divider()
    stats = workflow.get_approval_stats()
    cols = st.columns(len(stats))
    for idx, (status, count) in enumerate(stats.items()):
        cols[idx].metric(status, count)
