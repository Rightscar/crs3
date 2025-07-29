import React from 'react';
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Chip,
  Divider,
  Paper,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import {
  Chat as ChatIcon,
  Handshake as HandshakeIcon,
  Psychology as PsychologyIcon,
  FavoriteBorder as HeartIcon,
  HeartBroken as HeartBrokenIcon,
  Groups as GroupsIcon,
  AutoAwesome as SparkleIcon,
} from '@mui/icons-material';
import { formatDistanceToNow } from 'date-fns';
import { Character, CharacterInteraction } from '../../types/character';

const FeedContainer = styled(Box)(({ theme }) => ({
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
}));

const FeedList = styled(List)(({ theme }) => ({
  flexGrow: 1,
  overflow: 'auto',
  padding: 0,
  '&::-webkit-scrollbar': {
    width: '8px',
  },
  '&::-webkit-scrollbar-track': {
    background: theme.palette.background.default,
  },
  '&::-webkit-scrollbar-thumb': {
    background: theme.palette.divider,
    borderRadius: '4px',
  },
}));

const ActivityItem = styled(ListItem)(({ theme }) => ({
  flexDirection: 'column',
  alignItems: 'stretch',
  padding: theme.spacing(2),
  '&:hover': {
    backgroundColor: theme.palette.action.hover,
  },
}));

const ActivityHeader = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(1),
  marginBottom: theme.spacing(1),
}));

const ActivityContent = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(1.5),
  backgroundColor: theme.palette.grey[50],
  border: `1px solid ${theme.palette.divider}`,
  borderRadius: theme.shape.borderRadius,
  marginTop: theme.spacing(1),
}));

const EmotionChip = styled(Chip)(({ theme }) => ({
  height: 24,
  fontSize: '0.75rem',
}));

interface ActivityFeedProps {
  activities: CharacterInteraction[];
  characters: Character[];
}

const ActivityFeed: React.FC<ActivityFeedProps> = ({ activities, characters }) => {
  const getCharacterName = (characterId: string) => {
    const character = characters.find(c => c.id === characterId);
    return character?.name || 'Unknown';
  };

  const getInteractionIcon = (type: string) => {
    switch (type) {
      case 'greeting':
        return <HandshakeIcon />;
      case 'chat':
        return <ChatIcon />;
      case 'conflict':
        return <HeartBrokenIcon />;
      case 'collaboration':
        return <GroupsIcon />;
      case 'emotional_support':
        return <HeartIcon />;
      case 'discussion':
      case 'debate':
        return <PsychologyIcon />;
      default:
        return <SparkleIcon />;
    }
  };

  const getInteractionColor = (type: string): 'default' | 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success' => {
    switch (type) {
      case 'greeting':
        return 'info';
      case 'conflict':
        return 'error';
      case 'collaboration':
        return 'success';
      case 'emotional_support':
        return 'secondary';
      default:
        return 'default';
    }
  };

  const formatActivityMessage = (activity: CharacterInteraction) => {
    const participants = activity.participants || [];
    if (participants.length < 2) return 'Unknown interaction';

    const initiator = participants.find(p => p.role === 'initiator');
    const responder = participants.find(p => p.role === 'responder');

    if (!initiator || !responder) return 'Unknown interaction';

    const actionVerbs: Record<string, string> = {
      greeting: 'greeted',
      chat: 'chatted with',
      conflict: 'had a conflict with',
      collaboration: 'collaborated with',
      emotional_support: 'provided support to',
      discussion: 'discussed with',
      debate: 'debated with',
    };

    const verb = actionVerbs[activity.interaction_type] || 'interacted with';
    return `${initiator.name} ${verb} ${responder.name}`;
  };

  const getDominantEmotion = (emotionalStates: Record<string, Record<string, number>>) => {
    const emotions: Record<string, number> = {};
    
    // Aggregate emotions across all participants
    Object.values(emotionalStates).forEach(state => {
      Object.entries(state).forEach(([emotion, value]) => {
        emotions[emotion] = (emotions[emotion] || 0) + value;
      });
    });

    // Find dominant emotion
    let maxEmotion = '';
    let maxValue = 0;
    Object.entries(emotions).forEach(([emotion, value]) => {
      if (value > maxValue) {
        maxEmotion = emotion;
        maxValue = value;
      }
    });

    return maxEmotion;
  };

  const getEmotionColor = (emotion: string): 'default' | 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success' => {
    const emotionColors: Record<string, any> = {
      joy: 'success',
      sadness: 'info',
      anger: 'error',
      fear: 'warning',
      surprise: 'secondary',
      disgust: 'default',
    };
    return emotionColors[emotion] || 'default';
  };

  const getRelationshipChangeText = (change: any) => {
    if (!change) return null;
    
    const strengthDelta = change.strength_delta || 0;
    const trustDelta = change.trust_delta || 0;

    if (strengthDelta > 0.05) return '💕 Relationship strengthened';
    if (strengthDelta < -0.05) return '💔 Relationship weakened';
    if (trustDelta > 0.03) return '🤝 Trust increased';
    if (trustDelta < -0.03) return '😟 Trust decreased';
    
    return null;
  };

  return (
    <FeedContainer>
      <Typography variant="h6" gutterBottom>
        Live Activity Feed
      </Typography>

      <FeedList>
        {activities.length === 0 ? (
          <Box textAlign="center" py={4}>
            <SparkleIcon sx={{ fontSize: 48, color: 'text.disabled' }} />
            <Typography color="textSecondary">
              No activities yet
            </Typography>
            <Typography variant="caption" color="textSecondary">
              Character interactions will appear here
            </Typography>
          </Box>
        ) : (
          activities.map((activity, index) => {
            const dominantEmotion = getDominantEmotion(activity.emotional_states || {});
            const relationshipChange = getRelationshipChangeText(activity.relationship_change);
            
            return (
              <React.Fragment key={activity.id || index}>
                <ActivityItem>
                  <ActivityHeader>
                    <Avatar sx={{ width: 32, height: 32, bgcolor: `${getInteractionColor(activity.interaction_type)}.main` }}>
                      {getInteractionIcon(activity.interaction_type)}
                    </Avatar>
                    <Box flexGrow={1}>
                      <Typography variant="body2" fontWeight="medium">
                        {formatActivityMessage(activity)}
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        {activity.timestamp ? formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true }) : 'Just now'}
                      </Typography>
                    </Box>
                  </ActivityHeader>

                  {activity.content && (
                    <ActivityContent elevation={0}>
                      <Typography variant="body2" color="textSecondary" fontStyle="italic">
                        "{activity.content}"
                      </Typography>
                      {activity.response && (
                        <Typography variant="body2" color="textSecondary" fontStyle="italic" mt={1}>
                          → "{activity.response}"
                        </Typography>
                      )}
                    </ActivityContent>
                  )}

                  <Box display="flex" gap={1} mt={1} flexWrap="wrap">
                    {dominantEmotion && (
                      <EmotionChip
                        label={dominantEmotion}
                        size="small"
                        color={getEmotionColor(dominantEmotion)}
                        variant="outlined"
                      />
                    )}
                    {activity.sentiment !== undefined && (
                      <EmotionChip
                        label={activity.sentiment > 0 ? 'Positive' : activity.sentiment < 0 ? 'Negative' : 'Neutral'}
                        size="small"
                        color={activity.sentiment > 0 ? 'success' : activity.sentiment < 0 ? 'error' : 'default'}
                        variant="outlined"
                      />
                    )}
                  </Box>

                  {relationshipChange && (
                    <Typography variant="caption" color="primary" mt={1}>
                      {relationshipChange}
                    </Typography>
                  )}
                </ActivityItem>
                {index < activities.length - 1 && <Divider />}
              </React.Fragment>
            );
          })
        )}
      </FeedList>
    </FeedContainer>
  );
};

export default ActivityFeed;