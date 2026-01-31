"use client";

import { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { Experience } from '@/types';

mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || '';

if (!mapboxgl.accessToken) {
    console.error('⚠️ NEXT_PUBLIC_MAPBOX_TOKEN no está configurado');
}

interface MapPanelProps {
    experiences: Experience[];
    selectedExperience?: Experience | null;
    onExperienceSelect?: (experience: Experience) => void;
}

export function MapPanel({
    experiences,
    selectedExperience,
    onExperienceSelect
}: MapPanelProps) {
    const mapContainer = useRef<HTMLDivElement>(null);
    const map = useRef<mapboxgl.Map | null>(null);
    const markersRef = useRef<mapboxgl.Marker[]>([]);
    const [mapLoaded, setMapLoaded] = useState(false);
    const [validExperiencesCount, setValidExperiencesCount] = useState(0);

    // Inicializar mapa
    useEffect(() => {
        if (!mapContainer.current || map.current) return;

        console.log('🗺️ Inicializando mapa Mapbox');
        console.log('Token configurado:', mapboxgl.accessToken ? 'Sí ✓' : 'No ✗');
        console.log('Contenedor:', mapContainer.current);
        console.log('Dimensiones contenedor:', {
            width: mapContainer.current?.offsetWidth,
            height: mapContainer.current?.offsetHeight
        });

        map.current = new mapboxgl.Map({
            container: mapContainer.current,
            style: 'mapbox://styles/mapbox/streets-v12',
            center: [-86.8771, 21.0365], // Aeropuerto Internacional de Cancún
            zoom: 6
        });

        map.current.addControl(new mapboxgl.NavigationControl(), 'top-right');

        map.current.on('load', () => {
            console.log('✅ Mapa Mapbox cargado exitosamente');
            setMapLoaded(true);
        });

        return () => {
            map.current?.remove();
            map.current = null;
        };
    }, []);

    // Actualizar marcadores cuando cambian las experiencias
    useEffect(() => {
        if (!map.current || !mapLoaded) {
            console.log('⏸️ Mapa no listo:', { mapExists: !!map.current, mapLoaded });
            return;
        }

        console.log(`📍 Actualizando marcadores - ${experiences.length} experiencias`);

        // Limpiar marcadores anteriores
        console.log(`🗑️ Limpiando ${markersRef.current.length} marcadores anteriores`);
        markersRef.current.forEach(marker => marker.remove());
        markersRef.current = [];

        if (experiences.length === 0) {
            console.log('📭 No hay experiencias para mostrar');
            return;
        }
        // Crear bounds para ajustar el mapa
        const bounds = new mapboxgl.LngLatBounds();
        let validCoordinatesCount = 0;
        let invalidCoordinatesCount = 0;

        // Agregar marcadores
        experiences.forEach((exp, index) => {
            if (!exp.lat || !exp.lon) {
                console.warn(`⚠️ Experiencia "${exp.name}" no tiene coordenadas válidas:`, { lat: exp.lat, lon: exp.lon });
                invalidCoordinatesCount++;
                return;
            }
            validCoordinatesCount++;

            // Crear elemento del marcador
            const el = document.createElement('div');
            el.className = 'custom-marker';
            el.innerHTML = `
        <div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold text-sm shadow-lg border-2 border-white cursor-pointer hover:bg-blue-600 transition-colors">
          ${index + 1}
        </div>
      `;

            // Crear popup
            const popup = new mapboxgl.Popup({ offset: 25 }).setHTML(`
        <div class="p-2 max-w-[200px]">
          <h3 class="font-semibold text-sm mb-1">${exp.name}</h3>
          <p class="text-xs text-gray-500 mb-1">${exp.location}</p>
          ${exp.duration ? `<p class="text-xs text-gray-400">⏱️ ${exp.duration}</p>` : ''}
        </div>
      `);

            // Crear marcador
            const marker = new mapboxgl.Marker(el)
                .setLngLat([exp.lon, exp.lat])
                .setPopup(popup)
                .addTo(map.current!);

            // Click handler
            el.addEventListener('click', () => {
                onExperienceSelect?.(exp);
            });

            markersRef.current.push(marker);
            bounds.extend([exp.lon, exp.lat]);
        });

        console.log(`✅ Marcadores creados: ${validCoordinatesCount} válidos, ${invalidCoordinatesCount} sin coordenadas`);
        // Actualizar estado con el número de experiencias válidas
        setValidExperiencesCount(validCoordinatesCount);

        // Ajustar vista para mostrar todos los marcadores
        if (validCoordinatesCount > 0) {
            console.log('🎯 Ajustando mapa a nuevas experiencias');
            console.log('Bounds:', {
                sw: bounds.getSouthWest(),
                ne: bounds.getNorthEast()
            });

            // Usar setTimeout para asegurar que los marcadores estén renderizados
            setTimeout(() => {
                if (map.current) {
                    map.current.fitBounds(bounds, {
                        padding: {
                            top: 50,
                            bottom: 50,
                            left: 50,
                            right: 50
                        },
                        maxZoom: 12,
                        duration: 1000,  // Animación de 1 segundo
                        essential: true  // No se puede interrumpir
                    });
                }
            }, 100);  // Pequeño delay para asegurar que DOM esté actualizado
        }
    }, [experiences, mapLoaded, onExperienceSelect]);

    // Centrar en experiencia seleccionada
    useEffect(() => {
        if (!map.current || !selectedExperience?.lat || !selectedExperience?.lon) return;

        map.current.flyTo({
            center: [selectedExperience.lon, selectedExperience.lat],
            zoom: 12,
            duration: 1500
        });

        // Abrir popup del marcador seleccionado
        const index = experiences.findIndex(e => e.id === selectedExperience.id);
        if (index !== -1 && markersRef.current[index]) {
            markersRef.current[index].togglePopup();
        }
    }, [selectedExperience, experiences]);

    return (
        <div className="relative w-full h-full" style={{ width: '100%', height: '100%' }}>
            <div ref={mapContainer} className="absolute inset-0" style={{ width: '100%', height: '100%' }} />

            {/* Leyenda */}
            {validExperiencesCount > 0 && (
                <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-lg p-3 max-w-[250px]">
                    <p className="text-sm font-medium mb-2">
                        {validExperiencesCount} experiencias en el mapa
                    </p>
                    {experiences.length > validExperiencesCount && (
                        <p className="text-xs text-amber-600 mb-2">
                            ⚠️ {experiences.length - validExperiencesCount} experiencias sin coordenadas
                        </p>
                    )}
                    <div className="text-xs text-gray-500">
                        Click en un marcador para ver detalles
                    </div>
                </div>
            )}

            {/* Placeholder cuando no hay experiencias */}
            {experiences.length === 0 && (
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <div className="bg-white/90 rounded-lg p-6 text-center shadow-lg">
                        <p className="text-gray-600">
                            🗺️ Las experiencias aparecerán aquí
                        </p>
                        <p className="text-sm text-gray-400 mt-1">
                            Busca algo en el chat para comenzar
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
}