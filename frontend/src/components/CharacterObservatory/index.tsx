import React, { useState, useEffect } from 'react';
import { Box, Grid, Paper, Typography, Container } from '@mui/material';
import { styled } from '@mui/material/styles';
import CharacterList from './CharacterList';
import RelationshipMap from './RelationshipMap';
import ActivityFeed from './ActivityFeed';
import InteractionPanel from './InteractionPanel';
import { useWebSocket } from '../../hooks/useWebSocket';
import { Character, CharacterInteraction, Relationship } from '../../types/character';

const ObservatoryContainer = styled(Container)(({ theme }) => ({
  paddingTop: theme.spacing(4),
  paddingBottom: theme.spacing(4),
  height: '100vh',
  display: 'flex',
  flexDirection: 'column',
}));

const MainGrid = styled(Grid)(({ theme }) => ({
  flexGrow: 1,
  height: '100%',
  overflow: 'hidden',
}));

const SectionPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(2),
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  overflow: 'hidden',
}));

interface CharacterObservatoryProps {
  ecosystemId: string;
}

const CharacterObservatory: React.FC<CharacterObservatoryProps> = ({ ecosystemId }) => {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [selectedCharacters, setSelectedCharacters] = useState<[string?, string?]>([]);
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [activities, setActivities] = useState<CharacterInteraction[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // WebSocket connection for real-time updates
  const { messages, connectionStatus } = useWebSocket(
    `/api/v1/interactions/ws/${ecosystemId}`
  );

  // Load initial data
  useEffect(() => {
    const loadEcosystemData = async () => {
      try {
        // Fetch characters
        const charResponse = await fetch(`/api/v1/ecosystems/${ecosystemId}/characters`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        });
        const charData = await charResponse.json();
        setCharacters(charData.items || []);

        // Fetch relationships
        const relResponse = await fetch(`/api/v1/ecosystems/${ecosystemId}/relationships`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        });
        const relData = await relResponse.json();
        setRelationships(relData.items || []);

        setIsLoading(false);
      } catch (error) {
        console.error('Failed to load ecosystem data:', error);
        setIsLoading(false);
      }
    };

    loadEcosystemData();
  }, [ecosystemId]);

  // Handle WebSocket messages
  useEffect(() => {
    if (messages.length > 0) {
      const latestMessage = messages[messages.length - 1];
      
      if (latestMessage.type === 'ecosystem_event') {
        const event = latestMessage.event;
        
        switch (event.type) {
          case 'character_interaction':
            // Add to activity feed
            setActivities(prev => [event.data, ...prev].slice(0, 50));
            
            // Update relationships if needed
            if (event.data.relationship_change) {
              updateRelationship(event.data);
            }
            break;
            
          case 'character_state_change':
            // Update character state
            updateCharacterState(event.data);
            break;
            
          case 'relationship_change':
            // Update relationship
            updateRelationshipFromEvent(event.data);
            break;
        }
      }
    }
  }, [messages]);

  const updateRelationship = (interactionData: any) => {
    // Update relationship strength based on interaction
    const { participants, relationship_change } = interactionData;
    if (participants.length >= 2 && relationship_change) {
      setRelationships(prev => {
        return prev.map(rel => {
          if ((rel.character_a_id === participants[0].id && rel.character_b_id === participants[1].id) ||
              (rel.character_a_id === participants[1].id && rel.character_b_id === participants[0].id)) {
            return {
              ...rel,
              strength: relationship_change.new_strength || rel.strength,
              trust: relationship_change.new_trust || rel.trust,
            };
          }
          return rel;
        });
      });
    }
  };

  const updateCharacterState = (stateData: any) => {
    const { character_id, changes } = stateData;
    setCharacters(prev => {
      return prev.map(char => {
        if (char.id === character_id) {
          return {
            ...char,
            ...changes,
          };
        }
        return char;
      });
    });
  };

  const updateRelationshipFromEvent = (eventData: any) => {
    const { character_a_id, character_b_id, changes } = eventData;
    setRelationships(prev => {
      return prev.map(rel => {
        if ((rel.character_a_id === character_a_id && rel.character_b_id === character_b_id) ||
            (rel.character_a_id === character_b_id && rel.character_b_id === character_a_id)) {
          return {
            ...rel,
            ...changes,
          };
        }
        return rel;
      });
    });
  };

  const handleCharacterSelect = (characterId: string) => {
    setSelectedCharacters(prev => {
      if (prev[0] === characterId) {
        return [undefined, prev[1]];
      } else if (prev[1] === characterId) {
        return [prev[0], undefined];
      } else if (!prev[0]) {
        return [characterId, prev[1]];
      } else if (!prev[1]) {
        return [prev[0], characterId];
      } else {
        return [characterId, undefined];
      }
    });
  };

  const handleInteraction = async (interaction: any) => {
    try {
      const response = await fetch('/api/v1/interactions/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(interaction),
      });

      if (!response.ok) {
        throw new Error('Failed to process interaction');
      }

      const result = await response.json();
      console.log('Interaction result:', result);
    } catch (error) {
      console.error('Interaction error:', error);
    }
  };

  return (
    <ObservatoryContainer maxWidth="xl">
      <Typography variant="h4" component="h1" gutterBottom>
        Character Observatory
      </Typography>
      
      <Typography variant="body2" color="textSecondary" gutterBottom>
        Ecosystem: {ecosystemId} | Status: {connectionStatus}
      </Typography>

      <MainGrid container spacing={2}>
        {/* Left Panel - Character List */}
        <Grid item xs={12} md={3}>
          <SectionPaper elevation={2}>
            <CharacterList
              characters={characters}
              selectedCharacters={selectedCharacters}
              onCharacterSelect={handleCharacterSelect}
              isLoading={isLoading}
            />
          </SectionPaper>
        </Grid>

        {/* Center Panel - Relationship Map */}
        <Grid item xs={12} md={6}>
          <SectionPaper elevation={2}>
            <RelationshipMap
              characters={characters}
              relationships={relationships}
              selectedCharacters={selectedCharacters}
              onCharacterSelect={handleCharacterSelect}
            />
          </SectionPaper>
        </Grid>

        {/* Right Panel - Activity Feed */}
        <Grid item xs={12} md={3}>
          <SectionPaper elevation={2}>
            <ActivityFeed
              activities={activities}
              characters={characters}
            />
          </SectionPaper>
        </Grid>

        {/* Bottom Panel - Interaction Controls */}
        {selectedCharacters[0] && selectedCharacters[1] && (
          <Grid item xs={12}>
            <SectionPaper elevation={2}>
              <InteractionPanel
                character1={characters.find(c => c.id === selectedCharacters[0])}
                character2={characters.find(c => c.id === selectedCharacters[1])}
                onInteraction={handleInteraction}
              />
            </SectionPaper>
          </Grid>
        )}
      </MainGrid>
    </ObservatoryContainer>
  );
};

export default CharacterObservatory;