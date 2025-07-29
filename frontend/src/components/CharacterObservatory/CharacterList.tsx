import React from 'react';
import {
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Avatar,
  Typography,
  Box,
  Chip,
  LinearProgress,
  Skeleton,
  IconButton,
  Tooltip,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import {
  Person as PersonIcon,
  Battery20 as BatteryLowIcon,
  Battery50 as BatteryMedIcon,
  Battery80 as BatteryHighIcon,
  BatteryFull as BatteryFullIcon,
} from '@mui/icons-material';
import { Character } from '../../types/character';

const CharacterListContainer = styled(Box)(({ theme }) => ({
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
}));

const ListContainer = styled(List)(({ theme }) => ({
  flexGrow: 1,
  overflow: 'auto',
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

const CharacterListItem = styled(ListItem)<{ selected?: boolean }>(({ theme, selected }) => ({
  borderRadius: theme.shape.borderRadius,
  marginBottom: theme.spacing(1),
  cursor: 'pointer',
  transition: 'all 0.2s ease',
  backgroundColor: selected ? theme.palette.action.selected : 'transparent',
  '&:hover': {
    backgroundColor: theme.palette.action.hover,
  },
}));

const CharacterAvatar = styled(Avatar)(({ theme }) => ({
  width: 48,
  height: 48,
  fontSize: '1.2rem',
  fontWeight: 'bold',
}));

const EnergyBar = styled(LinearProgress)(({ theme }) => ({
  height: 6,
  borderRadius: 3,
  marginTop: theme.spacing(0.5),
}));

interface CharacterListProps {
  characters: Character[];
  selectedCharacters: [string?, string?];
  onCharacterSelect: (characterId: string) => void;
  isLoading: boolean;
}

const CharacterList: React.FC<CharacterListProps> = ({
  characters,
  selectedCharacters,
  onCharacterSelect,
  isLoading,
}) => {
  const getEnergyIcon = (energy: number) => {
    if (energy >= 0.8) return <BatteryFullIcon />;
    if (energy >= 0.5) return <BatteryHighIcon />;
    if (energy >= 0.3) return <BatteryMedIcon />;
    return <BatteryLowIcon />;
  };

  const getEnergyColor = (energy: number): 'success' | 'warning' | 'error' => {
    if (energy >= 0.5) return 'success';
    if (energy >= 0.3) return 'warning';
    return 'error';
  };

  const getCharacterInitials = (name: string) => {
    return name
      .split(' ')
      .map(word => word[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const getPersonalityChip = (character: Character) => {
    const traits = character.personality_traits;
    if (!traits) return null;

    // Find dominant trait
    let dominantTrait = '';
    let maxValue = 0;
    
    Object.entries(traits).forEach(([trait, value]) => {
      if (value > maxValue && Math.abs(value - 0.5) > 0.2) {
        maxValue = value;
        dominantTrait = trait;
      }
    });

    const traitLabels: Record<string, string> = {
      openness: 'Creative',
      conscientiousness: 'Organized',
      extraversion: 'Outgoing',
      agreeableness: 'Friendly',
      neuroticism: 'Sensitive',
    };

    if (dominantTrait && maxValue > 0.7) {
      return (
        <Chip
          label={traitLabels[dominantTrait] || dominantTrait}
          size="small"
          color="primary"
          variant="outlined"
        />
      );
    }

    return null;
  };

  if (isLoading) {
    return (
      <CharacterListContainer>
        <Typography variant="h6" gutterBottom>
          Characters
        </Typography>
        <ListContainer>
          {[1, 2, 3].map((i) => (
            <ListItem key={i}>
              <ListItemAvatar>
                <Skeleton variant="circular" width={48} height={48} />
              </ListItemAvatar>
              <ListItemText
                primary={<Skeleton width="60%" />}
                secondary={<Skeleton width="80%" />}
              />
            </ListItem>
          ))}
        </ListContainer>
      </CharacterListContainer>
    );
  }

  return (
    <CharacterListContainer>
      <Typography variant="h6" gutterBottom>
        Characters ({characters.length})
      </Typography>
      
      <ListContainer>
        {characters.map((character) => {
          const isSelected = selectedCharacters.includes(character.id);
          const selectionIndex = selectedCharacters.indexOf(character.id);
          
          return (
            <CharacterListItem
              key={character.id}
              selected={isSelected}
              onClick={() => onCharacterSelect(character.id)}
            >
              <ListItemAvatar>
                <CharacterAvatar
                  sx={{
                    bgcolor: isSelected 
                      ? selectionIndex === 0 ? 'primary.main' : 'secondary.main'
                      : 'grey.400'
                  }}
                >
                  {character.avatar_url ? (
                    <img src={character.avatar_url} alt={character.name} />
                  ) : (
                    getCharacterInitials(character.name)
                  )}
                </CharacterAvatar>
              </ListItemAvatar>
              
              <ListItemText
                primary={
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography variant="subtitle1" component="span">
                      {character.name}
                    </Typography>
                    {getPersonalityChip(character)}
                  </Box>
                }
                secondary={
                  <Box>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Tooltip title={`Social Energy: ${Math.round(character.social_energy * 100)}%`}>
                        <Box display="flex" alignItems="center">
                          {getEnergyIcon(character.social_energy)}
                        </Box>
                      </Tooltip>
                      <Box flexGrow={1}>
                        <EnergyBar
                          variant="determinate"
                          value={character.social_energy * 100}
                          color={getEnergyColor(character.social_energy)}
                        />
                      </Box>
                    </Box>
                    <Typography variant="caption" color="textSecondary">
                      {character.interaction_count || 0} interactions
                    </Typography>
                  </Box>
                }
              />
              
              {isSelected && (
                <Chip
                  label={selectionIndex === 0 ? '1' : '2'}
                  size="small"
                  color={selectionIndex === 0 ? 'primary' : 'secondary'}
                />
              )}
            </CharacterListItem>
          );
        })}
      </ListContainer>
      
      {characters.length === 0 && (
        <Box textAlign="center" py={4}>
          <PersonIcon sx={{ fontSize: 48, color: 'text.disabled' }} />
          <Typography color="textSecondary">
            No characters in this ecosystem
          </Typography>
        </Box>
      )}
    </CharacterListContainer>
  );
};

export default CharacterList;