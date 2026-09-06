Feature: Configured API health
  Scenario: Service is available
    Given a configured API health endpoint
    When I request the health endpoint
    Then the HTTP status is 200
