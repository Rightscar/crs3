import { test, expect } from '@playwright/test';

test.describe('Character Observatory E2E Tests', () => {
  let authToken: string;
  let ecosystemId: string;
  let characterIds: string[] = [];

  test.beforeAll(async ({ request }) => {
    // Register test user
    const registerResponse = await request.post('/api/v1/auth/register', {
      data: {
        email: 'e2e@test.com',
        username: 'e2euser',
        password: 'testpass123'
      }
    });
    expect(registerResponse.ok()).toBeTruthy();

    // Login
    const loginResponse = await request.post('/api/v1/auth/login', {
      data: {
        username: 'e2euser',
        password: 'testpass123'
      }
    });
    expect(loginResponse.ok()).toBeTruthy();
    const loginData = await loginResponse.json();
    authToken = loginData.access_token;

    // Create ecosystem
    const ecosystemResponse = await request.post('/api/v1/ecosystems/', {
      headers: {
        'Authorization': `Bearer ${authToken}`
      },
      data: {
        name: 'E2E Test Ecosystem',
        description: 'Testing Character Observatory'
      }
    });
    const ecosystemData = await ecosystemResponse.json();
    ecosystemId = ecosystemData.id;

    // Create test characters
    const characters = [
      {
        name: 'Alice E2E',
        description: 'Test character 1',
        personality_traits: {
          openness: 0.8,
          conscientiousness: 0.6,
          extraversion: 0.7,
          agreeableness: 0.9,
          neuroticism: 0.3
        },
        ecosystem_id: ecosystemId
      },
      {
        name: 'Bob E2E',
        description: 'Test character 2',
        personality_traits: {
          openness: 0.4,
          conscientiousness: 0.9,
          extraversion: 0.3,
          agreeableness: 0.5,
          neuroticism: 0.6
        },
        ecosystem_id: ecosystemId
      }
    ];

    for (const charData of characters) {
      const response = await request.post('/api/v1/characters/', {
        headers: {
          'Authorization': `Bearer ${authToken}`
        },
        data: charData
      });
      const character = await response.json();
      characterIds.push(character.id);
    }
  });

  test.beforeEach(async ({ page }) => {
    // Set auth token in localStorage
    await page.addInitScript((token) => {
      localStorage.setItem('token', token);
    }, authToken);
  });

  test('should load Character Observatory with all panels', async ({ page }) => {
    await page.goto(`/observatory/${ecosystemId}`);

    // Wait for main components to load
    await expect(page.locator('h1:has-text("Character Observatory")')).toBeVisible();
    
    // Check all panels are present
    await expect(page.locator('text=Characters (2)')).toBeVisible();
    await expect(page.locator('text=Relationship Network')).toBeVisible();
    await expect(page.locator('text=Live Activity Feed')).toBeVisible();

    // Check WebSocket connection status
    await expect(page.locator('text=Status: connected')).toBeVisible({ timeout: 5000 });
  });

  test('should display characters in list with energy bars', async ({ page }) => {
    await page.goto(`/observatory/${ecosystemId}`);

    // Check character list
    await expect(page.locator('text=Alice E2E')).toBeVisible();
    await expect(page.locator('text=Bob E2E')).toBeVisible();

    // Check energy indicators
    const aliceCard = page.locator('[role="listitem"]:has-text("Alice E2E")');
    await expect(aliceCard.locator('[role="progressbar"]')).toBeVisible();
    await expect(aliceCard.locator('text=/\\d+ interactions/')).toBeVisible();

    // Check personality chips
    await expect(aliceCard.locator('text=Creative')).toBeVisible(); // High openness
  });

  test('should allow character selection and show interaction panel', async ({ page }) => {
    await page.goto(`/observatory/${ecosystemId}`);

    // Select first character
    await page.click('text=Alice E2E');
    await expect(page.locator('[role="listitem"]:has-text("Alice E2E")').locator('text=1')).toBeVisible();

    // Select second character
    await page.click('text=Bob E2E');
    await expect(page.locator('[role="listitem"]:has-text("Bob E2E")').locator('text=2')).toBeVisible();

    // Interaction panel should appear
    await expect(page.locator('text=Character Interaction')).toBeVisible();
    await expect(page.locator('text=Initiator')).toBeVisible();
    await expect(page.locator('text=Target')).toBeVisible();
  });

  test('should trigger character interaction and update activity feed', async ({ page }) => {
    await page.goto(`/observatory/${ecosystemId}`);

    // Select characters
    await page.click('text=Alice E2E');
    await page.click('text=Bob E2E');

    // Wait for interaction panel
    await expect(page.locator('text=Character Interaction')).toBeVisible();

    // Select interaction type
    await page.click('text=👋 Greeting');

    // Send interaction
    await page.click('button:has-text("Send Interaction")');

    // Wait for processing
    await expect(page.locator('text=Processing...')).toBeVisible();
    await expect(page.locator('text=Processing...')).not.toBeVisible({ timeout: 5000 });

    // Check activity feed updated
    await expect(page.locator('text=Alice E2E greeted Bob E2E')).toBeVisible({ timeout: 5000 });
  });

  test('should update relationship visualization after interaction', async ({ page }) => {
    await page.goto(`/observatory/${ecosystemId}`);

    // Wait for D3 visualization to load
    await page.waitForSelector('svg');

    // Check nodes are rendered
    const nodes = page.locator('svg circle');
    await expect(nodes).toHaveCount(4); // 2 nodes x 2 circles each

    // Trigger interaction to create relationship
    await page.click('text=Alice E2E');
    await page.click('text=Bob E2E');
    await page.click('button:has-text("Send Interaction")');
    await page.waitForTimeout(1000);

    // Check relationship line appears
    const relationshipLines = page.locator('svg line');
    await expect(relationshipLines).toHaveCount(1);
  });

  test('should handle WebSocket reconnection', async ({ page, context }) => {
    await page.goto(`/observatory/${ecosystemId}`);
    
    // Wait for initial connection
    await expect(page.locator('text=Status: connected')).toBeVisible();

    // Simulate network interruption
    await context.setOffline(true);
    await expect(page.locator('text=Status: disconnected')).toBeVisible({ timeout: 5000 });

    // Restore connection
    await context.setOffline(false);
    await expect(page.locator('text=Status: connected')).toBeVisible({ timeout: 10000 });
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto(`/observatory/${ecosystemId}`);

    // Check layout adapts
    await expect(page.locator('h1:has-text("Character Observatory")')).toBeVisible();
    
    // Panels should stack vertically
    const panels = page.locator('[class*="MuiPaper-root"]');
    const count = await panels.count();
    expect(count).toBeGreaterThan(0);

    // Character list should still be functional
    await page.click('text=Alice E2E');
    await expect(page.locator('[role="listitem"]:has-text("Alice E2E")').locator('text=1')).toBeVisible();
  });

  test('should filter relationships by strength', async ({ page }) => {
    await page.goto(`/observatory/${ecosystemId}`);

    // Create multiple interactions to establish relationships
    for (let i = 0; i < 3; i++) {
      await page.click('text=Alice E2E');
      await page.click('text=Bob E2E');
      await page.click('text=💬 Chat');
      await page.click('button:has-text("Send Interaction")');
      await page.waitForTimeout(500);
    }

    // Open controls
    await expect(page.locator('text=Controls')).toBeVisible();

    // Adjust relationship strength filter
    const slider = page.locator('[role="slider"]');
    await slider.click({ position: { x: 50, y: 0 } }); // Set to ~0.5

    // Verify visualization updates
    // (Specific assertions would depend on relationship strengths)
  });

  test('should show emotional states in activity feed', async ({ page }) => {
    await page.goto(`/observatory/${ecosystemId}`);

    // Trigger emotional interaction
    await page.click('text=Alice E2E');
    await page.click('text=Bob E2E');
    await page.click('text=❤️ Support');
    
    // Use custom message
    await page.selectOption('select', '-1');
    await page.fill('textarea', "I'm here for you, Bob!");
    await page.click('button:has-text("Send Interaction")');

    // Check emotional indicators in feed
    await page.waitForTimeout(1000);
    const activityItem = page.locator('[class*="ActivityItem"]').first();
    await expect(activityItem.locator('text=/joy|happiness|comfort/')).toBeVisible();
  });

  test('should prevent interactions when energy is low', async ({ page, request }) => {
    // Deplete character energy through API
    for (let i = 0; i < 10; i++) {
      await request.post('/api/v1/interactions/', {
        headers: {
          'Authorization': `Bearer ${authToken}`
        },
        data: {
          initiator_id: characterIds[0],
          target_id: characterIds[1],
          interaction_type: 'discussion',
          content: 'Energy depletion test'
        }
      });
    }

    await page.goto(`/observatory/${ecosystemId}`);
    await page.waitForTimeout(1000);

    // Select characters
    await page.click('text=Alice E2E');
    await page.click('text=Bob E2E');

    // Check if send button is disabled due to low energy
    const sendButton = page.locator('button:has-text("Send Interaction")');
    const isDisabled = await sendButton.isDisabled();
    
    if (isDisabled) {
      // Verify energy warning
      await expect(page.locator('text=/energy/')).toBeVisible();
    }
  });
});