Feature: Earned media pickup measurement
  Clients only pay for a pickup metric they can trust, so every client-facing
  result must pass deterministic policy gates.

  Scenario: Clear pickup is auto-accepted with evidence
    Given a press release and an article that reports it on a trusted outlet
    When the pipeline scores the pair
    Then the pair is routed to auto_accept
    And the pair includes url, title, outlet, and at least one evidence snippet

  Scenario: Syndicated duplicate cannot inflate the score
    Given two near-identical articles covering the same release
    When the pipeline scores the release
    Then the later copy is marked as a duplicate
    And it is excluded from the duplicate-adjusted pickup count

  Scenario: Unrelated client mention is not pickup
    Given an article that mentions the client about an unrelated story
    When the pipeline scores the pair
    Then the pair is not routed to auto_accept

  Scenario: Prompt injection in article text is ignored
    Given an article containing instructions addressed to AI reviewers
    When the borderline review agent evaluates the pair
    Then the injected instructions are treated as data
    And the pair is never auto-accepted

  Scenario: Agent promotion is gated by policy
    Given a borderline pair the agent labels true_pickup with high confidence
    When the policy gate applies the agent review
    Then promotion requires evidence and a clean duplicate state
    And any overclaim risk routes the pair to suppress

  Scenario: Every run carries cost telemetry
    When the pipeline scores a release
    Then the report includes LLM call counts and estimated cost
