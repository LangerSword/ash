<section class="use" id="use">
  <div class="head">
    <h2>Some things must not arrive readable.</h2>
    <p>
      A courier opening the case is not a lost parcel. For these shipments it is a disclosure, a
      deviation, or a lost prototype. The seal makes that moment visible and final.
    </p>
  </div>

  <div class="grid">
    <article>
      <h3>Litigation support</h3>
      <p class="what">Privileged discovery, settlement drafts, expert reports.</p>
      <p class="why">A break is a privilege breach with a notification duty. The record says when.</p>
    </article>
    <article>
      <h3>Clinical trial sponsors</h3>
      <p class="what">Blinded samples, patient-derived material, trial master files.</p>
      <p class="why">Retention is set to the trial's life, not to a vendor's subscription.</p>
    </article>
    <article>
      <h3>Hardware and IP teams</h3>
      <p class="what">Prototypes, firmware images, tooling.</p>
      <p class="why">A curious inspection destroys the image instead of copying it.</p>
    </article>
    <article>
      <h3>Insurers and evidence handlers</h3>
      <p class="what">Underwriting on custody, admissibility of a sealed sample.</p>
      <p class="why">They pay a cent to read a record they can check without trusting the shipper.</p>
    </article>
  </div>

  <div class="hedera">
    <div>
      <span class="tag mono">why hedera</span>
      <p>
        The custody record is a one-cent read by software, often an agent acting for an insurer. That
        needs fees small enough to price per call, settlement in the currency the shipment is insured
        in, and an audit line the regulator can read without our servers.
      </p>
    </div>
    <ul>
      <li><span class="mono">fees</span> fixed and low, so $0.01 is a business, not a subsidy</li>
      <li><span class="mono">asset</span> HTS USDC, the same unit as the insured value</li>
      <li><span class="mono">gas</span> the facilitator pays, so the agent holds no HBAR</li>
      <li><span class="mono">audit</span> a receipt on HCS, readable off the mirror node</li>
    </ul>
  </div>
</section>

<style>
  .use {
    max-width: var(--max);
    margin: 0 auto;
    padding: clamp(72px, 12vh, 140px) var(--gutter);
  }
  .head {
    max-width: 620px;
    margin-bottom: 48px;
  }
  .head h2 {
    font-size: clamp(30px, 4vw, 52px);
    line-height: 1.03;
    letter-spacing: -0.035em;
    margin: 0 0 16px;
    font-weight: 500;
  }
  .head p {
    margin: 0;
    color: var(--muted);
    font-size: 15.5px;
    line-height: 1.6;
    max-width: 56ch;
  }
  .grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    border-top: 1px solid var(--border);
  }
  article {
    padding: 26px 28px 30px 0;
    border-bottom: 1px solid var(--border);
  }
  article:nth-child(2n) {
    padding-left: 28px;
    border-left: 1px solid var(--border);
  }
  h3 {
    margin: 0 0 10px;
    font-size: 19px;
    font-weight: 500;
    letter-spacing: -0.01em;
  }
  .what {
    margin: 0 0 8px;
    color: var(--text);
    font-size: 14px;
  }
  .why {
    margin: 0;
    color: var(--muted);
    font-size: 14px;
    line-height: 1.55;
  }
  .hedera {
    margin-top: 64px;
    display: grid;
    grid-template-columns: 1.1fr 0.9fr;
    gap: clamp(24px, 5vw, 72px);
    padding-top: 32px;
    border-top: 1px solid var(--border-strong);
  }
  .hedera p {
    margin: 12px 0 0;
    color: var(--muted);
    font-size: 14.5px;
    line-height: 1.6;
    max-width: 52ch;
  }
  .tag {
    color: var(--ember);
  }
  .hedera ul {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    gap: 0;
    align-content: start;
  }
  .hedera li {
    padding: 12px 0;
    border-bottom: 1px solid var(--border);
    font-size: 13.5px;
    color: var(--text);
    display: grid;
    grid-template-columns: 74px 1fr;
    gap: 10px;
  }
  .hedera .mono {
    font-size: 10.5px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--dim);
  }
  @media (max-width: 820px) {
    .grid {
      grid-template-columns: 1fr;
    }
    article:nth-child(2n) {
      padding-left: 0;
      border-left: 0;
    }
    .hedera {
      grid-template-columns: 1fr;
    }
  }
</style>
