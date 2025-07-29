import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  Chip,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  IconButton,
  Tooltip,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import {
  Send as SendIcon,
  SwapHoriz as SwapIcon,
  Psychology as PsychologyIcon,
  AutoAwesome as AutoAwesomeIcon,
} from '@mui/icons-material';
import { Character } from '../../types/character';

const PanelContainer = styled(Box)(({ theme }) => ({
  padding: theme.spacing(2),
}));

const CharacterCard = styled(Card)(({ theme }) => ({
  marginBottom: theme.spacing(2),
  backgroundColor: theme.palette.grey[50],
}));

const InteractionTypeChip = styled(Chip)(({ theme }) => ({
  margin: theme.spacing(0.5),
}));

interface InteractionPanelProps {
  character1?: Character;
  character2?: Character;
  onInteraction: (interaction: any) => Promise<void>;
}

const InteractionPanel: React.FC<InteractionPanelProps> = ({
  character1,
  character2,
  onInteraction,
}) => {
  const [interactionType, setInteractionType] = useState('chat');
  const [customMessage, setCustomMessage] = useState('');
  const [useCustomMessage, setUseCustomMessage] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [swapped, setSwapped] = useState(false);

  const interactionTypes = [
    { value: 'greeting', label: 'Greeting', icon: '👋', description: 'A friendly hello' },
    { value: 'chat', label: 'Chat', icon: '💬', description: 'Casual conversation' },
    { value: 'discussion', label: 'Discussion', icon: '🗣️', description: 'Serious talk' },
    { value: 'debate', label: 'Debate', icon: '⚖️', description: 'Exchange of ideas' },
    { value: 'collaboration', label: 'Collaboration', icon: '🤝', description: 'Work together' },
    { value: 'emotional_support', label: 'Support', icon: '❤️', description: 'Offer comfort' },
    { value: 'conflict', label: 'Conflict', icon: '⚡', description: 'Disagreement' },
  ];

  const suggestedMessages: Record<string, string[]> = {
    greeting: [
      "Hello! How are you doing today?",
      "Hey there! It's nice to see you.",
      "Good to see you! What have you been up to?",
    ],
    chat: [
      "What do you think about the weather today?",
      "Have you read any good books lately?",
      "I've been thinking about our last conversation.",
    ],
    discussion: [
      "I'd like to discuss something important with you.",
      "What are your thoughts on this matter?",
      "Let's talk about our plans moving forward.",
    ],
    debate: [
      "I respectfully disagree with your perspective.",
      "Let me present an alternative viewpoint.",
      "How do you defend your position on this?",
    ],
    collaboration: [
      "Would you like to work together on this?",
      "I think we could achieve great things as a team.",
      "Let's combine our strengths for this project.",
    ],
    emotional_support: [
      "I'm here for you if you need to talk.",
      "You seem troubled. Is everything okay?",
      "I want you to know that I care about you.",
    ],
    conflict: [
      "I'm upset about what happened earlier.",
      "We need to address this issue between us.",
      "I can't agree with what you're saying.",
    ],
  };

  const handleSwapCharacters = () => {
    setSwapped(!swapped);
  };

  const initiator = swapped ? character2 : character1;
  const target = swapped ? character1 : character2;

  const handleSendInteraction = async () => {
    if (!initiator || !target) return;

    setIsLoading(true);
    setError(null);

    const message = useCustomMessage 
      ? customMessage 
      : suggestedMessages[interactionType][0];

    try {
      await onInteraction({
        initiator_id: initiator.id,
        target_id: target.id,
        interaction_type: interactionType,
        content: message,
        context: {
          manual_trigger: true,
          timestamp: new Date().toISOString(),
        },
      });

      // Reset form
      setCustomMessage('');
      setUseCustomMessage(false);
    } catch (err) {
      setError('Failed to process interaction. Please try again.');
      console.error('Interaction error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const getPersonalityInsight = (character: Character) => {
    const traits = character.personality_traits;
    if (!traits) return null;

    const insights = [];
    
    if (traits.agreeableness > 0.7) {
      insights.push('Very friendly and cooperative');
    } else if (traits.agreeableness < 0.3) {
      insights.push('Can be challenging and skeptical');
    }

    if (traits.neuroticism > 0.7) {
      insights.push('Emotionally sensitive');
    }

    if (traits.extraversion > 0.7) {
      insights.push('Outgoing and energetic');
    } else if (traits.extraversion < 0.3) {
      insights.push('Reserved and introspective');
    }

    return insights.length > 0 ? insights.join(', ') : 'Balanced personality';
  };

  if (!character1 || !character2) {
    return (
      <PanelContainer>
        <Alert severity="info">
          Select two characters to enable interactions
        </Alert>
      </PanelContainer>
    );
  }

  return (
    <PanelContainer>
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
        <Typography variant="h6">
          Character Interaction
        </Typography>
        <Tooltip title="Get AI suggestions">
          <IconButton size="small">
            <AutoAwesomeIcon />
          </IconButton>
        </Tooltip>
      </Box>

      <Grid container spacing={2} alignItems="center">
        <Grid item xs={5}>
          <CharacterCard variant="outlined">
            <CardContent>
              <Chip 
                label="Initiator" 
                color="primary" 
                size="small" 
                sx={{ mb: 1 }}
              />
              <Typography variant="subtitle1" fontWeight="bold">
                {initiator?.name}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                Energy: {Math.round((initiator?.social_energy || 0) * 100)}%
              </Typography>
              <Typography variant="caption" display="block" color="textSecondary">
                {getPersonalityInsight(initiator)}
              </Typography>
            </CardContent>
          </CharacterCard>
        </Grid>

        <Grid item xs={2} textAlign="center">
          <IconButton onClick={handleSwapCharacters} color="primary">
            <SwapIcon />
          </IconButton>
        </Grid>

        <Grid item xs={5}>
          <CharacterCard variant="outlined">
            <CardContent>
              <Chip 
                label="Target" 
                color="secondary" 
                size="small" 
                sx={{ mb: 1 }}
              />
              <Typography variant="subtitle1" fontWeight="bold">
                {target?.name}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                Energy: {Math.round((target?.social_energy || 0) * 100)}%
              </Typography>
              <Typography variant="caption" display="block" color="textSecondary">
                {getPersonalityInsight(target)}
              </Typography>
            </CardContent>
          </CharacterCard>
        </Grid>
      </Grid>

      <Box mt={3}>
        <Typography variant="subtitle2" gutterBottom>
          Interaction Type
        </Typography>
        <Box display="flex" flexWrap="wrap">
          {interactionTypes.map((type) => (
            <InteractionTypeChip
              key={type.value}
              label={`${type.icon} ${type.label}`}
              onClick={() => setInteractionType(type.value)}
              color={interactionType === type.value ? 'primary' : 'default'}
              variant={interactionType === type.value ? 'filled' : 'outlined'}
            />
          ))}
        </Box>
      </Box>

      <Box mt={3}>
        <Typography variant="subtitle2" gutterBottom>
          Message
        </Typography>
        
        {!useCustomMessage ? (
          <Box>
            <Select
              fullWidth
              value={0}
              onChange={(e) => {
                const index = e.target.value as number;
                if (index === -1) {
                  setUseCustomMessage(true);
                }
              }}
            >
              {suggestedMessages[interactionType].map((msg, index) => (
                <MenuItem key={index} value={index}>
                  {msg}
                </MenuItem>
              ))}
              <MenuItem value={-1}>
                <em>Write custom message...</em>
              </MenuItem>
            </Select>
          </Box>
        ) : (
          <Box>
            <TextField
              fullWidth
              multiline
              rows={2}
              value={customMessage}
              onChange={(e) => setCustomMessage(e.target.value)}
              placeholder="Type your custom message..."
              variant="outlined"
            />
            <Button
              size="small"
              onClick={() => {
                setUseCustomMessage(false);
                setCustomMessage('');
              }}
              sx={{ mt: 1 }}
            >
              Use suggested messages
            </Button>
          </Box>
        )}
      </Box>

      {error && (
        <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Box mt={3} display="flex" justifyContent="space-between" alignItems="center">
        <Typography variant="caption" color="textSecondary">
          This will consume social energy from both characters
        </Typography>
        
        <Button
          variant="contained"
          color="primary"
          startIcon={isLoading ? <CircularProgress size={20} /> : <SendIcon />}
          onClick={handleSendInteraction}
          disabled={
            isLoading || 
            (useCustomMessage && !customMessage.trim()) ||
            (initiator?.social_energy || 0) < 0.1 ||
            (target?.social_energy || 0) < 0.1
          }
        >
          {isLoading ? 'Processing...' : 'Send Interaction'}
        </Button>
      </Box>
    </PanelContainer>
  );
};

export default InteractionPanel;