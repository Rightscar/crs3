import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { Box, Typography, Paper, Slider, FormControlLabel, Switch } from '@mui/material';
import { styled } from '@mui/material/styles';
import { Character, Relationship } from '../../types/character';

const MapContainer = styled(Box)(({ theme }) => ({
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
}));

const VisualizationContainer = styled(Box)(({ theme }) => ({
  flexGrow: 1,
  position: 'relative',
  overflow: 'hidden',
  backgroundColor: theme.palette.background.default,
  borderRadius: theme.shape.borderRadius,
  border: `1px solid ${theme.palette.divider}`,
}));

const ControlsContainer = styled(Paper)(({ theme }) => ({
  position: 'absolute',
  top: theme.spacing(2),
  right: theme.spacing(2),
  padding: theme.spacing(2),
  backgroundColor: 'rgba(255, 255, 255, 0.9)',
  backdropFilter: 'blur(10px)',
  zIndex: 10,
}));

interface RelationshipMapProps {
  characters: Character[];
  relationships: Relationship[];
  selectedCharacters: [string?, string?];
  onCharacterSelect: (characterId: string) => void;
}

interface D3Node extends d3.SimulationNodeDatum {
  id: string;
  name: string;
  social_energy: number;
  personality_traits?: Record<string, number>;
  group?: number;
}

interface D3Link extends d3.SimulationLinkDatum<D3Node> {
  strength: number;
  trust: number;
  relationship_type: string;
}

const RelationshipMap: React.FC<RelationshipMapProps> = ({
  characters,
  relationships,
  selectedCharacters,
  onCharacterSelect,
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [showLabels, setShowLabels] = useState(true);
  const [linkStrengthThreshold, setLinkStrengthThreshold] = useState(0);

  useEffect(() => {
    if (!svgRef.current || characters.length === 0) return;

    // Clear previous visualization
    d3.select(svgRef.current).selectAll('*').remove();

    const svg = d3.select(svgRef.current);
    const width = svgRef.current.clientWidth;
    const height = svgRef.current.clientHeight;

    // Create container groups
    const g = svg.append('g');
    
    // Add zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.5, 3])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });
    
    svg.call(zoom);

    // Prepare data
    const nodes: D3Node[] = characters.map(char => ({
      id: char.id,
      name: char.name,
      social_energy: char.social_energy,
      personality_traits: char.personality_traits,
    }));

    const links: D3Link[] = relationships
      .filter(rel => Math.abs(rel.strength) >= linkStrengthThreshold)
      .map(rel => ({
        source: rel.character_a_id,
        target: rel.character_b_id,
        strength: rel.strength,
        trust: rel.trust,
        relationship_type: rel.relationship_type,
      }));

    // Create force simulation
    const simulation = d3.forceSimulation<D3Node>(nodes)
      .force('link', d3.forceLink<D3Node, D3Link>(links)
        .id(d => d.id)
        .distance(d => 100 - Math.abs(d.strength) * 50)
        .strength(d => Math.abs(d.strength))
      )
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(40));

    // Create link elements
    const linkGroup = g.append('g').attr('class', 'links');
    
    const link = linkGroup.selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', d => {
        if (d.strength > 0.5) return '#4caf50';
        if (d.strength > 0) return '#2196f3';
        if (d.strength > -0.5) return '#ff9800';
        return '#f44336';
      })
      .attr('stroke-width', d => Math.abs(d.strength) * 5 + 1)
      .attr('stroke-opacity', 0.6)
      .attr('stroke-dasharray', d => d.trust < 0.3 ? '5,5' : 'none');

    // Create node group
    const nodeGroup = g.append('g').attr('class', 'nodes');
    
    const node = nodeGroup.selectAll('g')
      .data(nodes)
      .join('g')
      .attr('cursor', 'pointer')
      .call(d3.drag<SVGGElement, D3Node>()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended)
      );

    // Add circles for nodes
    node.append('circle')
      .attr('r', d => 20 + d.social_energy * 10)
      .attr('fill', d => {
        if (selectedCharacters[0] === d.id) return '#1976d2';
        if (selectedCharacters[1] === d.id) return '#dc004e';
        return '#757575';
      })
      .attr('stroke', '#fff')
      .attr('stroke-width', 3)
      .on('click', (event, d) => {
        event.stopPropagation();
        onCharacterSelect(d.id);
      });

    // Add energy indicator
    node.append('circle')
      .attr('r', d => (20 + d.social_energy * 10) - 3)
      .attr('fill', 'none')
      .attr('stroke', d => {
        if (d.social_energy > 0.7) return '#4caf50';
        if (d.social_energy > 0.3) return '#ff9800';
        return '#f44336';
      })
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', d => {
        const radius = (20 + d.social_energy * 10) - 3;
        const circumference = 2 * Math.PI * radius;
        const dashLength = circumference * d.social_energy;
        return `${dashLength} ${circumference - dashLength}`;
      })
      .attr('transform', 'rotate(-90)');

    // Add labels
    if (showLabels) {
      node.append('text')
        .text(d => d.name)
        .attr('text-anchor', 'middle')
        .attr('dy', d => 35 + d.social_energy * 10)
        .style('font-size', '12px')
        .style('font-weight', 'bold')
        .style('fill', '#333');
    }

    // Add personality indicator (dominant trait)
    node.each(function(d) {
      if (d.personality_traits) {
        const traits = d.personality_traits;
        let dominant = '';
        let maxValue = 0;
        
        Object.entries(traits).forEach(([trait, value]) => {
          if (value > maxValue && value > 0.7) {
            maxValue = value;
            dominant = trait;
          }
        });

        if (dominant) {
          const icons: Record<string, string> = {
            openness: '💡',
            conscientiousness: '📋',
            extraversion: '🗣️',
            agreeableness: '❤️',
            neuroticism: '😰',
          };

          d3.select(this).append('text')
            .text(icons[dominant] || '✨')
            .attr('text-anchor', 'middle')
            .attr('dy', 5)
            .style('font-size', '16px');
        }
      }
    });

    // Update positions on simulation tick
    simulation.on('tick', () => {
      link
        .attr('x1', d => (d.source as D3Node).x!)
        .attr('y1', d => (d.source as D3Node).y!)
        .attr('x2', d => (d.target as D3Node).x!)
        .attr('y2', d => (d.target as D3Node).y!);

      node.attr('transform', d => `translate(${d.x},${d.y})`);
    });

    // Drag functions
    function dragstarted(event: d3.D3DragEvent<SVGGElement, D3Node, D3Node>) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }

    function dragged(event: d3.D3DragEvent<SVGGElement, D3Node, D3Node>) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }

    function dragended(event: d3.D3DragEvent<SVGGElement, D3Node, D3Node>) {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }

    // Cleanup
    return () => {
      simulation.stop();
    };
  }, [characters, relationships, selectedCharacters, onCharacterSelect, showLabels, linkStrengthThreshold]);

  return (
    <MapContainer>
      <Typography variant="h6" gutterBottom>
        Relationship Network
      </Typography>
      
      <VisualizationContainer>
        <svg ref={svgRef} width="100%" height="100%" />
        
        <ControlsContainer elevation={3}>
          <Typography variant="subtitle2" gutterBottom>
            Controls
          </Typography>
          
          <FormControlLabel
            control={
              <Switch
                checked={showLabels}
                onChange={(e) => setShowLabels(e.target.checked)}
                size="small"
              />
            }
            label="Show Names"
          />
          
          <Box mt={2}>
            <Typography variant="caption" gutterBottom>
              Relationship Strength Filter
            </Typography>
            <Slider
              value={linkStrengthThreshold}
              onChange={(_, value) => setLinkStrengthThreshold(value as number)}
              min={0}
              max={1}
              step={0.1}
              valueLabelDisplay="auto"
              size="small"
            />
          </Box>
        </ControlsContainer>
      </VisualizationContainer>
      
      <Box mt={2}>
        <Typography variant="caption" color="textSecondary">
          Node size: Social energy | Line thickness: Relationship strength | Line color: Relationship quality
        </Typography>
      </Box>
    </MapContainer>
  );
};

export default RelationshipMap;